import os
import pyttsx3
import datetime
import speech_recognition as sr

speak = pyttsx3.init()
voices = speak.getProperty('voices')
speak.setProperty('voice',voices[2].id)
speak.setProperty('rate', 200)

def engine(command):
    speak.say(command)
    speak.runAndWait()

def greetings():
    time = datetime.datetime.now().strftime("%H:%M")
    if time < "12:00":
        engine("Good morning")
    elif time > "19:00":
        engine("Good afternoon")
    else:
        engine("Good evening")

def takecommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.pause_threshold = 0.7
        greetings()
        print("Activating")
        audio = r.listen(source)

        try:
            print("Recognizing...")
            query = r.recognize_google(audio, language='en-in')

        except:
            return "none"

        return query.lower()

while True:
    wake_up = takecommand()
    if "jarvis" in wake_up:
        print(query)
        # os.startfile("alexa.py")
    else:
        print("Nothing .......")