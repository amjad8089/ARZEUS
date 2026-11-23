import requests
from speech import speak


def get_weather(city):

    try:

        # Step 1: Get latitude and longitude
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"

        geo_response = requests.get(geo_url).json()

        if "results" not in geo_response:
            speak("Sorry, I couldn't find that city.")
            return

        latitude = geo_response["results"][0]["latitude"]
        longitude = geo_response["results"][0]["longitude"]

        # Step 2: Get weather
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={latitude}"
            f"&longitude={longitude}"
            f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
        )

        weather_response = requests.get(weather_url).json()

        current = weather_response["current"]

        temperature = current["temperature_2m"]
        humidity = current["relative_humidity_2m"]
        wind = current["wind_speed_10m"]
        code = current["weather_code"]

        weather = weather_description(code)

        message = (
            f"The current weather in {city} is {weather}. "
            f"The temperature is {temperature} degrees Celsius. "
            f"The humidity is {humidity} percent. "
            f"The wind speed is {wind} kilometers per hour."
        )

        speak(message)

    except Exception as e:

        print(e)

        speak("Unable to fetch weather information.")


def weather_description(code):

    descriptions = {

        0: "clear sky",

        1: "mainly clear",

        2: "partly cloudy",

        3: "overcast",

        45: "fog",

        48: "depositing rime fog",

        51: "light drizzle",

        53: "moderate drizzle",

        55: "dense drizzle",

        61: "light rain",

        63: "moderate rain",

        65: "heavy rain",

        71: "light snowfall",

        73: "moderate snowfall",

        75: "heavy snowfall",

        80: "rain showers",

        81: "moderate rain showers",

        82: "violent rain showers",

        95: "thunderstorm",

        96: "thunderstorm with hail",

        99: "heavy thunderstorm with hail"

    }

    return descriptions.get(code, "unknown weather")