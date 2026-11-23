import psutil
import platform
import shutil

from speech import speak


def battery():

    b = psutil.sensors_battery()

    if b:
        speak(f"Battery is {b.percent} percent.")

    else:
        speak("Battery information unavailable.")


def cpu():

    usage = psutil.cpu_percent()

    speak(f"CPU usage is {usage} percent.")


def memory():

    ram = psutil.virtual_memory()

    speak(f"RAM usage is {ram.percent} percent.")


def storage():

    total, used, free = shutil.disk_usage("C:\\")

    total_gb = total / (1024 ** 3)
    free_gb = free / (1024 ** 3)

    speak(
        f"Your C drive has {free_gb:.1f} gigabytes free "
        f"out of {total_gb:.1f} gigabytes."
    )


def windows_version():

    version = platform.win32_ver()[1]

    speak(f"Your Windows version is {version}.")