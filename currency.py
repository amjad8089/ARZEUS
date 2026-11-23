import requests
from speech import speak


def get_currency_rate():

    from_currency = input("Enter source currency: ").upper()
    to_currency = input("Enter target currency: ").upper()

    try:

        url = f"https://open.er-api.com/v6/latest/{from_currency}"

        response = requests.get(url)
        data = response.json()

        if data["result"] != "success":
            speak("Unable to get currency information.")
            return

        if to_currency not in data["rates"]:
            speak("I couldn't find that currency.")
            return

        rate = data["rates"][to_currency]

        speak(
            f"1 {from_currency} is equal to "
            f"{rate:.2f} {to_currency}."
        )

    except Exception as e:

        print("Currency Error:", e)

        speak("Unable to connect to the currency service.")