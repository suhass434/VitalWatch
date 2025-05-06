import speech_recognition as sr

r = sr.Recognizer()

with sr.Microphone() as mic:
    print("Say something...")
    audio = r.listen(mic)
print("Got audio, converting…")
print("You said:", r.recognize_google(audio))