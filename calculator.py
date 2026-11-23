from speech import speak


def calculate(expression):

    try:

        expression = expression.lower()

        expression = expression.replace("plus", "+")
        expression = expression.replace("minus", "-")
        expression = expression.replace("times", "*")
        expression = expression.replace("multiplied by", "*")
        expression = expression.replace("divided by", "/")

        result = eval(expression)

        speak(f"The answer is {result}")

    except:

        speak("Sorry, I couldn't calculate that.")