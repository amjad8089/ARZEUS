from datetime import datetime
from zoneinfo import ZoneInfo

from speech import speak


TIME_ZONES = {
    "kochi": "Asia/Kolkata",
    "india": "Asia/Kolkata",
    "london": "Europe/London",
    "new york": "America/New_York",
    "los angeles": "America/Los_Angeles",
    "dubai": "Asia/Dubai",
    "tokyo": "Asia/Tokyo",
    "singapore": "Asia/Singapore",
    "sydney": "Australia/Sydney",
    "paris": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "moscow": "Europe/Moscow"
}


def get_world_time(city):

    city = city.lower().strip()

    if city not in TIME_ZONES:
        speak("I don't have that location yet.")
        return

    time = datetime.now(
        ZoneInfo(TIME_ZONES[city])
    ).strftime("%I:%M %p")

    speak(f"The current time in {city.title()} is {time}.")