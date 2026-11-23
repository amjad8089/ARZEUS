import requests
from speech import speak


def get_country_info():

    country = input("Enter country name: ")

    try:

        # First get the country list
        response = requests.get(
            "https://countries.dev/countries",
            timeout=10
        )

        if response.status_code != 200:
            speak("Unable to connect to the country service.")
            return

        countries = response.json()

        # Find matching country
        country_data = None

        for item in countries:

            name = item.get("name", "")

            if name.lower() == country.lower():

                country_data = item
                break

        if country_data is None:

            speak("I couldn't find that country.")
            return

        name = country_data.get("name", "Unknown")
        capital = country_data.get("capital", "Unknown")
        population = country_data.get("population", 0)
        region = country_data.get("region", "Unknown")

        currencies = country_data.get("currencies", [])
        languages = country_data.get("languages", [])

        if currencies:

            currency = currencies[0].get(
                "name", "Unknown"
            )

        else:

            currency = "Unknown"

        if languages:

            language_list = ", ".join(
                language.get("name", "Unknown")
                for language in languages
            )

        else:

            language_list = "Unknown"

        speak(f"Country: {name}.")
        speak(f"Capital: {capital}.")
        speak(f"Population: {population:,}.")
        speak(f"Region: {region}.")
        speak(f"Currency: {currency}.")
        speak(f"Languages: {language_list}.")

    except Exception as e:

        print("Country Error:", repr(e))

        speak("Unable to get country information.")