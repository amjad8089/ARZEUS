
import datetime
import webbrowser
import subprocess

from speech import speak
from system import battery, cpu, memory, storage, windows_version
from diagnostics import run_diagnostics

import weather
from currency import get_currency_rate
from country import get_country_info
from world_time import get_world_time
from calculator import calculate
from converter import convert
from file_manager import create_folder, open_folder
from search import search


def execute(command):
    """Recognize and execute an ARZEUS command."""

    command = command.strip().lower()

    if not command:
        return True

    # ---------------- Basic Conversation ---------------- #

    if "hello" in command or "hi" in command:
        speak("Hello. How can I help you?")

    elif "how are you" in command:
        speak("I am functioning normally.")

    elif "who are you" in command:
        speak("I am Arzeus, your personal assistant.")

    elif "your creator" in command:
        speak("I was created by Amjad.")

    # ---------------- Diagnostics ---------------- #

    elif (
        "diagnostic" in command
        or "system health" in command
        or "device health" in command
    ):
        try:
            speak("Starting device diagnostics. Please wait.")

            result = run_diagnostics()

            print("\n========== ARZEUS DIAGNOSTICS ==========")
            print(f"Device: {result['report']['device']}")
            print(
                f"Operating system: "
                f"{result['report']['operating_system']}"
            )
            print(
                f"Warnings: {result['warning_count']}"
            )

            for finding in result["report"]["findings"]:
                print(
                    f"\n[{finding['severity']}] "
                    f"{finding['title']}"
                )
                print(f"Area: {finding['area']}")
                print(f"Evidence: {finding['evidence']}")
                print(
                    f"Possible cause: "
                    f"{finding['possible_cause']}"
                )
                print(
                    f"Recommended next step: "
                    f"{finding['recommended_next_step']}"
                )

            print("\nReports saved:")
            print(result["text_path"])
            print(result["json_path"])
            print("========================================")

            speak(
                "Diagnostics completed. "
                f"There are {result['warning_count']} "
                "warning or critical findings. "
                "The reports have been saved."
            )

        except Exception as exc:
            print(
                f"Diagnostic error: "
                f"{type(exc).__name__}: {exc}"
            )
            speak(
                "I could not complete the diagnostics. "
                "Please check the error message."
            )

    # ---------------- Conversion ---------------- #

    elif "convert" in command:
        convert(command)

    # ---------------- Date and Time ---------------- #

    elif "time in" in command:
        city = command.replace("time in", "", 1).strip()

        if city:
            get_world_time(city)
        else:
            speak("Please specify a city.")

    elif "time" in command:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {current_time}.")

    elif "date" in command:
        current_date = datetime.datetime.now().strftime("%d %B %Y")
        speak(f"Today's date is {current_date}.")

    # ---------------- System Information ---------------- #

    elif "battery" in command:
        battery()

    elif "cpu" in command:
        cpu()

    elif "memory" in command or "ram" in command:
        memory()

    elif "storage" in command:
        storage()

    elif "windows version" in command:
        windows_version()

    # ---------------- Websites ---------------- #

    elif "open google" in command:
        speak("Opening Google.")
        webbrowser.open("https://www.google.com")

    elif "open youtube" in command:
        speak("Opening YouTube.")
        webbrowser.open("https://www.youtube.com")

    elif "open chatgpt" in command:
        speak("Opening ChatGPT.")
        webbrowser.open("https://chatgpt.com")

    elif "open gemini" in command:
        speak("Opening Gemini.")
        webbrowser.open("https://gemini.google.com")

    elif "open copilot" in command:
        speak("Opening Copilot.")
        webbrowser.open("https://copilot.microsoft.com")

    # ---------------- Applications ---------------- #

    elif "open calculator" in command:
        speak("Opening Calculator.")
        subprocess.Popen(["calc.exe"])

    elif "open notepad" in command:
        speak("Opening Notepad.")
        subprocess.Popen(["notepad.exe"])

    # ---------------- Weather ---------------- #

    elif "weather" in command:
        city = command.replace("weather", "", 1).strip()

        if not city:
            city = input("Enter the city: ").strip()

        if city:
            weather.get_weather(city)
        else:
            speak("Please specify a city.")

    # ---------------- Currency and Country ---------------- #

    elif "currency" in command or "exchange rate" in command:
        get_currency_rate()

    elif "country information" in command or "country" in command:
        get_country_info()

    # ---------------- Calculator ---------------- #

    elif "calculate" in command:
        expression = command.replace("calculate", "", 1).strip()

        if expression:
            calculate(expression)
        else:
            speak("Please tell me what you want to calculate.")

    # ---------------- File Management ---------------- #

    elif "create folder" in command:
        name = command.replace("create folder", "", 1).strip()

        if name:
            create_folder(name)
        else:
            speak("Please tell me the folder name.")

    elif "open folder" in command:
        name = command.replace("open folder", "", 1).strip()

        if name:
            open_folder(name)
        else:
            speak("Please tell me the folder name.")

    # ---------------- Unknown Command ---------------- #

    else:
        return False

    return True
