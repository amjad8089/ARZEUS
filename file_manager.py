import os

from speech import speak


def create_folder(name):

    path = os.path.join(
        os.path.expanduser("~"),
        "Desktop",
        name
    )

    if os.path.exists(path):

        speak(f"The folder {name} already exists.")

    else:

        os.makedirs(path)

        speak(f"Folder {name} has been created on the Desktop.")


def open_folder(name):

    home = os.path.expanduser("~")

    folders = {
        "desktop": os.path.join(home, "Desktop"),
        "downloads": os.path.join(home, "Downloads"),
        "documents": os.path.join(home, "Documents"),
        "pictures": os.path.join(home, "Pictures"),
        "videos": os.path.join(home, "Videos"),
        "music": os.path.join(home, "Music")
    }

    name = name.lower().strip()

    # Common Windows folders
    if name in folders:

        path = folders[name]

        if os.path.exists(path):

            os.startfile(path)

            speak(f"Opening {name}.")

        else:

            speak(f"The {name} folder does not exist.")

        return

    # Check directly on C drive
    c_drive_path = os.path.join("C:\\", name)

    if os.path.exists(c_drive_path):

        os.startfile(c_drive_path)

        speak(f"Opening {name}.")

        return

    # Check Desktop
    desktop_path = os.path.join(
        home,
        "Desktop",
        name
    )

    if os.path.exists(desktop_path):

        os.startfile(desktop_path)

        speak(f"Opening {name}.")

        return

    speak(f"I couldn't find the folder {name}.")