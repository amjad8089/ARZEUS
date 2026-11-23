import config
from speech import speak

def authenticate():

    password = input("Enter Password : ")

    if password == config.PASSWORD:

        speak("Authentication Successful.")

        return True

    else:

        speak("Access Denied.")

        return False