"""Read-only, evidence-based diagnostics for ARZEUS on Windows."""

import json
import platform
import shutil
import socket
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

import psutil

BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "reports" / "diagnostics"


def _run_powershell(script, timeout=12):
    """Run a read-only PowerShell query. Return stdout or raise a useful error."""
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "PowerShell query failed").strip()
        raise RuntimeError(message[:500])
    return completed.stdout.strip()


def collect_diagnostics():
    """Collect read-only measurements; distinguish observations from possible causes."""
    now = datetime.now().astimezone()
    report = {
        "report_id": now.strftime("%Y%m%d_%H%M%S"),
        "created_at": now.isoformat(),
        "device": platform.node(),
        "operating_system": platform.platform(),
        "findings": [],
        "measurements": {},
        "limitations": [
            "All checks in this report are intended to be read-only.",
            "A warning is a reason to investigate, not a confirmed root cause.",
            "A single snapshot may miss intermittent problems.",
            "Hardware temperature readings depend on sensor and driver support.",
            "Drive-health information depends on what Windows and the storage device expose.",
            "Windows event logs may omit events that are inaccessible or outside the queried time window.",
        ],
    }
    findings = report["findings"]
    measurements = report["measurements"]

    def add(severity, area, title, evidence, possible_cause, next_step):
        findings.append({
            "severity": severity,
            "area": area,
            "title": title,
            "evidence": str(evidence),
            "possible_cause": str(possible_cause),
            "recommended_next_step": str(next_step),
        })

    # CPU
    try:
        cpu = psutil.cpu_percent(interval=1)
        measurements["cpu_percent"] = cpu
        if cpu >= 90:
            add("WARNING", "CPU", "High CPU usage", f"CPU usage was {cpu:.1f}% during a one-second sample.",
                "A demanding application, background task, or system activity may be using CPU resources.",
                "Check Task Manager and repeat measurements while the symptom occurs.")
        else:
            add("INFO", "CPU", "CPU usage measured", f"CPU usage was {cpu:.1f}% during a one-second sample.",
                "This short sample cannot establish whether CPU usage is persistently high.",
                "Repeat during any slowdown to compare results.")
    except Exception as exc:
        add("UNKNOWN", "CPU", "CPU check unavailable", type(exc).__name__,
            "CPU usage could not be collected.", "Check the Python environment and psutil installation.")

    # RAM
    try:
        ram = psutil.virtual_memory()
        measurements["ram"] = {"total_gb": round(ram.total / 2**30, 2),
                               "available_gb": round(ram.available / 2**30, 2),
                               "used_percent": ram.percent}
        if ram.percent >= 90:
            add("WARNING", "Memory", "High RAM usage", f"RAM usage is {ram.percent:.1f}%; {ram.available / 2**30:.2f} GB available.",
                "Applications or background processes may be consuming available memory.",
                "Inspect Task Manager before deciding whether any application should be closed.")
        else:
            add("INFO", "Memory", "RAM usage measured", f"RAM usage is {ram.percent:.1f}%; {ram.available / 2**30:.2f} GB available.",
                "This snapshot alone does not establish memory pressure.",
                "Compare with symptoms and repeat if performance issues occur.")
    except Exception as exc:
        add("UNKNOWN", "Memory", "RAM check unavailable", type(exc).__name__,
            "Memory information could not be collected.", "Check psutil and the Python environment.")

    # System drive and mounted partitions
    try:
        disk = shutil.disk_usage("C:\\")
        free_percent = disk.free / disk.total * 100 if disk.total else 0
        measurements["system_drive"] = {"path": "C:\\", "total_gb": round(disk.total / 2**30, 2),
            "used_gb": round(disk.used / 2**30, 2), "free_gb": round(disk.free / 2**30, 2),
            "free_percent": round(free_percent, 2)}
        if free_percent < 5:
            severity, title = "CRITICAL", "Very low free space"
            cause, next_step = "Low free space can interfere with updates and applications.", "Review storage usage and back up important files; do not delete files blindly."
        elif free_percent < 10:
            severity, title = "WARNING", "Low free space"
            cause, next_step = "Low free capacity may constrain operations that need temporary space.", "Review Windows Storage settings and identify large files safely."
        else:
            severity, title = "INFO", "System drive capacity measured"
            cause, next_step = "Free capacity does not measure drive speed or physical health.", "Investigate drive health separately if symptoms suggest a storage issue."
        add(severity, "Storage", title, f"C: has {disk.free / 2**30:.2f} GB free ({free_percent:.1f}%).", cause, next_step)
    except Exception as exc:
        add("UNKNOWN", "Storage", "System drive check unavailable", type(exc).__name__,
            "System drive capacity could not be read.", "Confirm the drive letter and access permissions.")

    try:
        partitions = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({"device": part.device, "mountpoint": part.mountpoint,
                    "filesystem": part.fstype, "total_gb": round(usage.total / 2**30, 2),
                    "free_gb": round(usage.free / 2**30, 2),
                    "free_percent": round(usage.free / usage.total * 100, 2) if usage.total else None})
            except (PermissionError, OSError):
                continue
        measurements["mounted_drives"] = partitions
    except Exception as exc:
        report["limitations"].append(f"Mounted-drive inventory incomplete: {type(exc).__name__}.")

    # Battery
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            measurements["battery"] = {"available": False}
            add("UNKNOWN", "Battery", "Battery information unavailable", "psutil did not expose battery information.",
                "Battery sensor data may be unsupported or unavailable.", "If battery behaviour is abnormal, inspect Windows power settings and generate a battery report.")
        else:
            measurements["battery"] = {"available": True, "percent": battery.percent, "plugged_in": battery.power_plugged,
                "seconds_left": battery.secsleft if battery.secsleft not in (psutil.POWER_TIME_UNKNOWN, psutil.POWER_TIME_UNLIMITED) else None}
            if battery.percent <= 10 and not battery.power_plugged:
                add("WARNING", "Battery", "Battery charge is low", f"Charge: {battery.percent:.1f}%; plugged in: False.",
                    "The battery has a low current charge; this does not indicate battery wear.", "Save work and connect power if appropriate.")
            else:
                add("INFO", "Battery", "Battery status measured", f"Charge: {battery.percent:.1f}%; plugged in: {battery.power_plugged}.",
                    "Charge percentage does not establish battery health or wear.", "Check battery health separately if runtime or charging is abnormal.")
    except Exception as exc:
        add("UNKNOWN", "Battery", "Battery check failed", type(exc).__name__,
            "Battery information could not be collected.", "Check Windows power settings and sensor support.")

    # OS and uptime
    try:
        uptime_hours = max(0, time.time() - psutil.boot_time()) / 3600
        measurements["windows"] = {"system": platform.system(), "release": platform.release(),
            "version": platform.version(), "architecture": platform.machine(), "uptime_hours": round(uptime_hours, 2)}
        add("INFO", "Operating system", "System information collected",
            f"{platform.system()} {platform.release()}; uptime approximately {uptime_hours:.1f} hours.",
            "Long uptime alone is not evidence of a problem.",
            "If troubleshooting a recent issue, note whether it began after a restart, update, or software change.")
    except Exception as exc:
        add("UNKNOWN", "Operating system", "OS check incomplete", type(exc).__name__,
            "Some operating-system details could not be collected.", "Check system permissions and the Python environment.")

    # Top processes by CPU and memory (CPU is a short sample, not a long-term average).
    try:
        process_rows = []
        for proc in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                info = proc.info
                mem = info.get("memory_info")
                process_rows.append({"pid": info["pid"], "name": info.get("name") or "Unknown",
                                     "memory_mb": round(mem.rss / 2**20, 1) if mem else None})
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        measurements["top_memory_processes"] = sorted(
            [p for p in process_rows if p["memory_mb"] is not None], key=lambda p: p["memory_mb"], reverse=True)[:10]
    except Exception as exc:
        measurements["top_memory_processes"] = []
        report["limitations"].append(f"Process inventory incomplete: {type(exc).__name__}.")

    # Network: DNS resolution and a short TCP connection attempt.
    try:
        started = time.perf_counter()
        resolved = socket.getaddrinfo("www.microsoft.com", 443, type=socket.SOCK_STREAM)
        dns_ms = round((time.perf_counter() - started) * 1000, 1)
        measurements["network_dns"] = {"host": "www.microsoft.com", "resolved": bool(resolved), "elapsed_ms": dns_ms}
        add("INFO", "Network", "DNS resolution succeeded", f"www.microsoft.com resolved successfully in {dns_ms:.1f} ms.",
            "Successful DNS resolution does not guarantee all internet services are reachable.",
            "If an application still cannot connect, test that service and the local network separately.")
    except Exception as exc:
        measurements["network_dns"] = {"host": "www.microsoft.com", "resolved": False, "error": type(exc).__name__}
        add("WARNING", "Network", "DNS resolution failed", f"Resolving www.microsoft.com failed ({type(exc).__name__}).",
            "Possible causes include no network connection, DNS configuration, VPN, firewall, or a temporary resolver issue.",
            "Check Wi-Fi/Ethernet and retry; then compare with another network or DNS diagnostic.")

    try:
        started = time.perf_counter()
        with socket.create_connection(("www.microsoft.com", 443), timeout=4):
            tcp_ms = round((time.perf_counter() - started) * 1000, 1)
        measurements["network_tcp"] = {"host": "www.microsoft.com", "port": 443, "connected": True, "elapsed_ms": tcp_ms}
        add("INFO", "Network", "HTTPS endpoint reachable", f"TCP connection to www.microsoft.com:443 succeeded in {tcp_ms:.1f} ms.",
            "One reachable endpoint does not prove every website or network path is healthy.",
            "If a particular service fails, test that destination specifically.")
    except Exception as exc:
        measurements["network_tcp"] = {"host": "www.microsoft.com", "port": 443, "connected": False, "error": type(exc).__name__}
        add("WARNING", "Network", "HTTPS endpoint connection failed", f"TCP connection to www.microsoft.com:443 failed ({type(exc).__name__}).",
            "Possible causes include connectivity issues, proxy/VPN settings, firewall rules, or temporary remote unavailability.",
            "Retry and test another known endpoint before concluding the network is faulty.")

    # Windows startup applications: inventory only, no changes.
    try:
        script = r"""
        $items = @()
        $paths = @(
          'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run',
          'HKLM:\Software\Microsoft\Windows\CurrentVersion\Run',
          'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run'
        )
        foreach ($path in $paths) {
          if (Test-Path $path) {
            $props = Get-ItemProperty -Path $path -ErrorAction SilentlyContinue
            if ($props) {
              foreach ($p in $props.PSObject.Properties) {
                if ($p.Name -notlike 'PS*') {
                  $items += [PSCustomObject]@{ registry_path=$path; name=$p.Name; command=[string]$p.Value }
                }
              }
            }
          }
        }
        ConvertTo-Json -InputObject @($items) -Depth 3 -Compress
        """
        output = _run_powershell(script, timeout=10)
        startup = json.loads(output) if output else []
        if isinstance(startup, dict):
            startup = [startup]
        measurements["startup_registry_entries"] = startup[:100]
        add("INFO", "Startup", "Startup registry inventory collected", f"Found {len(startup)} Run-key startup entries (up to 100 recorded).",
            "A startup entry is not inherently unwanted or harmful.",
            "Review names and publishers in Task Manager; do not disable entries solely because they are unfamiliar.")
    except Exception as exc:
        measurements["startup_registry_entries"] = []
        add("UNKNOWN", "Startup", "Startup inventory unavailable", type(exc).__name__,
            "The read-only registry query could not be completed.", "Review Startup apps in Windows Settings or Task Manager if needed.")

    # Recent Windows error/critical events (last 24 hours; bounded query).
    try:
        script = r"""
        $since = (Get-Date).AddHours(-24)
        $events = Get-WinEvent -FilterHashtable @{ LogName='System'; Level=1,2; StartTime=$since } -MaxEvents 40 -ErrorAction Stop |
          Select-Object TimeCreated, Id, ProviderName, LevelDisplayName, Message
        ConvertTo-Json -InputObject @($events) -Depth 3 -Compress
        """
        output = _run_powershell(script, timeout=18)
        events = json.loads(output) if output else []
        if isinstance(events, dict):
            events = [events]
        cleaned = []
        for event in events[:40]:
            cleaned.append({"time": str(event.get("TimeCreated", "")), "event_id": event.get("Id"),
                "provider": event.get("ProviderName"), "level": event.get("LevelDisplayName"),
                "message": str(event.get("Message") or "").replace("\r", " ").replace("\n", " ")[:500]})
        measurements["recent_system_events_24h"] = cleaned
        if cleaned:
            add("WARNING", "Windows events", "Recent system errors or critical events found",
                f"Found {len(cleaned)} System-log error/critical event(s) in the last 24 hours; details are in the JSON report.",
                "Events may be routine, unrelated, or symptoms of a real issue; event IDs and timing require context.",
                "Match event timestamps and providers to the user's symptoms before selecting a remedy.")
        else:
            add("INFO", "Windows events", "No matching recent system events returned",
                "No System-log error/critical events were returned by the bounded 24-hour query.",
                "This does not prove Windows has no errors; other logs and older events were not examined.",
                "If a problem persists, inspect Application logs and the time window around the incident.")
    except Exception as exc:
        measurements["recent_system_events_24h"] = []
        add("UNKNOWN", "Windows events", "System event-log query unavailable", type(exc).__name__,
            "The event-log query may be unsupported, inaccessible, or have returned no parseable output.",
            "Open Event Viewer manually or rerun the query with appropriate Windows permissions.")

    # Drive health from Windows Storage cmdlets, when available.
    try:
        script = r"""
        $items = @()
        if (Get-Command Get-PhysicalDisk -ErrorAction SilentlyContinue) {
          $items = Get-PhysicalDisk -ErrorAction Stop | Select-Object FriendlyName, MediaType, HealthStatus, OperationalStatus, Size
        }
        ConvertTo-Json -InputObject @($items) -Depth 3 -Compress
        """
        output = _run_powershell(script, timeout=12)
        drives = json.loads(output) if output else []
        if isinstance(drives, dict):
            drives = [drives]
        measurements["physical_drive_health"] = drives[:20]
        if not drives:
            add("UNKNOWN", "Drive health", "No physical-drive health data returned", "Windows did not return physical-drive entries through Get-PhysicalDisk.",
                "The storage provider, controller, virtualized storage, or device may not expose this information.",
                "Check the drive manufacturer's utility and back up important data if there are symptoms.")
        else:
            unhealthy = [d for d in drives if str(d.get("HealthStatus", "")).lower() not in ("healthy", "unknown", "") or
                         str(d.get("OperationalStatus", "")).lower() not in ("ok", "unknown", "")]
            if unhealthy:
                add("WARNING", "Drive health", "Drive status needs review", json.dumps(unhealthy, ensure_ascii=False),
                    "Windows reports a nonstandard health or operational status; interpretation depends on the device and driver.",
                    "Back up important data and confirm status with the manufacturer’s diagnostic tool before repair actions.")
            else:
                add("INFO", "Drive health", "Windows drive status collected", f"Collected status for {len(drives)} physical-drive entry/entries.",
                    "A Windows-reported healthy status does not guarantee the drive has no faults.",
                    "If symptoms persist, review SMART/diagnostic data using a trusted drive-manufacturer utility.")
    except Exception as exc:
        measurements["physical_drive_health"] = []
        add("UNKNOWN", "Drive health", "Physical-drive health query unavailable", type(exc).__name__,
            "This Windows installation or storage device may not expose the requested health data.",
            "Use the drive manufacturer's health utility; do not run repair operations without a backup and approval.")

    # Temperature sensors: psutil generally does not expose them on Windows.
    try:
        temps = psutil.sensors_temperatures()
        measurements["temperatures"] = {name: [vars(t) for t in values] for name, values in temps.items()} if temps else {}
        if temps:
            add("INFO", "Thermals", "Temperature sensor data available", f"Temperature data returned for {len(temps)} sensor group(s).",
                "Sensor labels and limits vary by hardware; a reading alone may need manufacturer thresholds.",
                "Compare sustained readings against the device manufacturer's specifications.")
        else:
            add("UNKNOWN", "Thermals", "Temperature readings unavailable", "No temperature sensors were exposed through psutil.",
                "Windows hardware/driver interfaces often do not expose CPU or GPU temperatures to psutil.",
                "If overheating is suspected, use the laptop manufacturer's trusted monitoring utility.")
    except Exception as exc:
        measurements["temperatures"] = {}
        add("UNKNOWN", "Thermals", "Temperature query unavailable", type(exc).__name__,
            "Temperature sensors could not be queried.", "Use a trusted manufacturer utility if thermal symptoms occur.")

    # Report summary; unknown checks remain explicit rather than silently passing.
    counts = {level: sum(1 for f in findings if f["severity"] == level)
              for level in ("CRITICAL", "WARNING", "INFO", "UNKNOWN")}
    report["summary"] = {"finding_count": len(findings), "severity_counts": counts,
                          "warning_count": counts["WARNING"] + counts["CRITICAL"],
                          "unknown_count": counts["UNKNOWN"]}
    return report


def save_report(report):
    """Save a JSON report and a human-readable text report."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_id = report["report_id"]
    json_path = REPORT_DIR / f"diagnostic_{report_id}.json"
    text_path = REPORT_DIR / f"diagnostic_{report_id}.txt"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    summary = report.get("summary", {})
    lines = ["ARZEUS DEVICE DIAGNOSTIC REPORT", "=" * 34,
             f"Report ID: {report_id}", f"Created: {report['created_at']}",
             f"Device: {report['device']}", f"Operating system: {report['operating_system']}", "",
             "SUMMARY", "-" * 34,
             f"Findings: {summary.get('finding_count', len(report['findings']))}",
             f"Critical: {summary.get('severity_counts', {}).get('CRITICAL', 0)}",
             f"Warnings: {summary.get('severity_counts', {}).get('WARNING', 0)}",
             f"Unknown/unavailable checks: {summary.get('unknown_count', 0)}", "",
             "FINDINGS", "-" * 34]
    for index, finding in enumerate(report["findings"], start=1):
        lines.extend([f"{index}. [{finding['severity']}] {finding['title']}",
                      f"   Area: {finding['area']}", f"   Evidence: {finding['evidence']}",
                      f"   Possible cause: {finding['possible_cause']}",
                      f"   Recommended next step: {finding['recommended_next_step']}", ""])
    lines.extend(["LIMITATIONS", "-" * 34])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(["", "TECHNICAL MEASUREMENTS", "-" * 34,
                  "Detailed measurements, process inventory, startup entries, and event records are in the JSON report."])
    text_path.write_text("\n".join(lines), encoding="utf-8")
    return text_path, json_path


def run_diagnostics():
    """Run checks, save reports, and return paths plus a compact summary."""
    report = collect_diagnostics()
    text_path, json_path = save_report(report)
    summary = report.get("summary", {})
    return {"report": report, "text_path": str(text_path), "json_path": str(json_path),
            "warning_count": summary.get("warning_count", 0),
            "unknown_count": summary.get("unknown_count", 0)}
