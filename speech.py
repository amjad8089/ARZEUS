import asyncio
import edge_tts
import pygame
import os
import speech_recognition as sr
import config

pygame.mixer.init()

VOICE_FILE = "voice.mp3"


async def generate_voice(text):
    communicate = edge_tts.Communicate(
        text=text,
        voice=config.VOICE_NAME
    )
    await communicate.save(VOICE_FILE)


def speak(text):
    print(f"{config.ASSISTANT_NAME}: {text}")

    asyncio.run(generate_voice(text))

    pygame.mixer.music.load(VOICE_FILE)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    pygame.mixer.music.unload()

    if os.path.exists(VOICE_FILE):
        os.remove(VOICE_FILE)


def listen():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)

    try:
        command = recognizer.recognize_google(audio)
        print("You:", command)
        return command.lower()

    except sr.UnknownValueError:
        return ""

    except sr.RequestError:
        speak("Speech recognition service is unavailable.")
        return ""