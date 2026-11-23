import datetime
import config

from speech import speak, listen
from auth import authenticate
from commands import execute
from search import search


print("=" * 50)
print("          ARZEUS AI ASSISTANT")
print("=" * 50)


# ---------------- Authentication ---------------- #

if not authenticate():
    print("Authentication Failed.")
    exit()


# ---------------- Greeting ---------------- #

hour = datetime.datetime.now().hour

if hour < 12:
    greeting="Good Morning"

elif hour < 18:
    greeting="Good Afternoon"

else:
    greeting="Good Evening"

speak(f"{greeting} {config.OWNER_NAME}. Arzeus is ready.")


# ---------------- Main Program ---------------- #

while True:

    print("\n========== MENU ==========")
    print("1. Voice Command")
    print("2. Text Command")
    print("3. Exit")
    print("==========================")

    choice = input("Select Mode: ")

    # ---------------- Voice Mode ---------------- #

    if choice == "1":

        print("Waiting for wake word.")

        while True:

            wake = listen()

            if wake == "":
                continue

            if config.WAKE_WORD in wake:

                speak("Yes?")

                command = listen()

                if command == "":
                    speak("I didn't hear any command.")
                    continue

                break

    # ---------------- Text Mode ---------------- #

    elif choice == "2":

        command = input("You : ").lower()

    # ---------------- Exit ---------------- #

    elif choice == "3":

        speak("See you later.")
        break

    else:

        print("Invalid Choice.")
        continue


    # ---------------- Exit Commands ---------------- #

    if any(word in command for word in ["exit", "quit", "bye", "stop"]):

        speak("See you soon.")
        break


    # ---------------- Execute Commands ---------------- #

    status = execute(command)

    if not status:

        search(command)