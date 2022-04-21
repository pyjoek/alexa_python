import speech_recognition as sr
from pyttsx3 import *
import datetime
import subprocess
import pywhatkit
import wikipedia
import pyjokes
import webbrowser

speak = pyttsx3.init()
voices = speak.getProperty('voices')
speak.setProperty('voice',voices[1].id)
speak.setProperty('rate', 150)

def greetings():
    time = datetime.datetime.now().strftime("%H:%M")
    if time < "12:00":
        engine("Good morning")
    elif time > "19:00":
        engine("Good afternoon")
    else:
        engine("Good evening")

    

def engine(command):
    speak.say(command)
    speak.runAndWait()

def takecommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        # r.energy_threshold = 10000
        # r.adjust_for_ambient_noise(source,2)
        r.pause_threshold = 0.7
        engine("jarvis at your service, How can i help you?")
        print("Listening....")
        audio = r.listen(source)

        try:
            print("Recognizing...")
            query = r.recognize_google(audio, language='en-in')
            time = datetime.datetime.now().strftime("%H:%M")
            if "time" in query:
                engine(f"The time is {time}")
                takecommand()
            elif "my name" in query:
                engine("Your name is Joel")
                takecommand()
            elif "love you" in query:
                engine("i love you too")
                takecommand()
            elif "lock screen" in query:
                subprocess.call("suspend")
                takecommand()
            elif "learning today" in query:
                engine("we are going to learn to create an AI as me")
                takecommand()
            elif "exit" in query or "quit" in query or "goodbye" in query:
                engine("Goodbye")
            elif "say" in query:
                say = query.replace("say"," ")
                engine(query)
                takecommand()
            elif "search for" in query:
                say = query.replace("search for"," ")
                say = wikipedia.summary(say, 1)
                engine(say)
                takecommand()
            elif "play" in query:
                say = query.replace("play"," ")
                pywhatkit.playonyt(say)
                takecommand()
            elif "google" in query:
                webbrowser.open("google.com")
                takecommand()
            elif "youtube" in query:
                webbrowser.open("youtube.com")
                takecommand()
            

        except sr.UnknownValueError:
            engine("Could not hear that, Try saying again")
            takecommand()

        except sr.RequestError:
            engine("Make Sure that you have a good Internet connection")
            takecommand()

        except Exception as ex:
            print("An exception occured",ex)

takecommand()