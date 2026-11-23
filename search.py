import requests
import webbrowser
from urllib.parse import quote

from speech import speak


def search(query):

    speak("Searching Wikipedia.")

    try:

        # Convert spaces to URL-safe format
        title = quote(query)

        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

        headers = {
            "User-Agent": "JarvisAI/1.0"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:

            data = response.json()

            if "extract" in data:

                speak(data["extract"])

                return

        speak("I couldn't find a Wikipedia article. Opening Google Search.")

        webbrowser.open(
            "https://www.google.com/search?q=" +
            query.replace(" ", "+")
        )

    except Exception as e:

        print("ERROR:", e)

        speak("Unable to reach Wikipedia. Opening Google Search.")

        webbrowser.open(
            "https://www.google.com/search?q=" +
            query.replace(" ", "+")
        )