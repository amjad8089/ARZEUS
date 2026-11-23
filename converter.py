from speech import speak


def convert(command):

    try:

        words = command.lower().split()

        value = float(words[1])

        from_unit = words[2]
        to_unit = words[4]

        # Kilometer to Mile
        if from_unit in ["km", "kilometer", "kilometers"] and to_unit in ["mile", "miles"]:
            result = value * 0.621371

        # Mile to Kilometer
        elif from_unit in ["mile", "miles"] and to_unit in ["km", "kilometer", "kilometers"]:
            result = value * 1.60934

        # Kilogram to Pound
        elif from_unit in ["kg", "kilogram", "kilograms"] and to_unit in ["lb", "lbs", "pound", "pounds"]:
            result = value * 2.20462

        # Pound to Kilogram
        elif from_unit in ["lb", "lbs", "pound", "pounds"] and to_unit in ["kg", "kilogram", "kilograms"]:
            result = value * 0.453592

        # Celsius to Fahrenheit
        elif from_unit in ["c", "celsius"] and to_unit in ["f", "fahrenheit"]:
            result = (value * 9 / 5) + 32

        # Fahrenheit to Celsius
        elif from_unit in ["f", "fahrenheit"] and to_unit in ["c", "celsius"]:
            result = (value - 32) * 5 / 9

        # Meter to Feet
        elif from_unit in ["m", "meter", "meters"] and to_unit in ["ft", "feet"]:
            result = value * 3.28084

        # Feet to Meter
        elif from_unit in ["ft", "feet"] and to_unit in ["m", "meter", "meters"]:
            result = value * 0.3048

        else:
            speak("Sorry, I don't support that conversion yet.")
            return

        speak(f"{value} {from_unit} is equal to {round(result, 2)} {to_unit}")

    except:

        speak("Sorry, I couldn't understand the conversion.")