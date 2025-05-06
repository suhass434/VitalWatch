import speech_recognition as sr
import asyncio
import edge_tts
import tempfile
import os

from .llm_client import query_llm, summarize_output
from .parser import parse_response
from .executor import is_safe, execute
from .logger import log_interaction
from .config import FORCE_CONFIRM, USE_SAFE_FLAG
from aioconsole import ainput

VOICE_NAME = "en-US-AriaNeural"  # You can change this voice if desired
VOICE_MODE = False

async def speak(text: str):
    communicate = edge_tts.Communicate(text, voice=VOICE_NAME)
    tmp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    await communicate.save(tmp_audio.name)
    os.system(f'play "{tmp_audio.name}"')  # You can also use `playsound` or other

def get_distro():
    return input("Enter your OS/distribution (e.g., Ubuntu 22.04): ").strip()

def listen_voice(recognizer, microphone):
    print("Listening…")
    try:
        audio = recognizer.listen(microphone)
        text = recognizer.recognize_google(audio).lower()
        print("You said:", text)
        return text
    except sr.UnknownValueError:
        print("Sorry, could not understand.")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results: {e}")
        return ""

async def process_user_input(user_text, os_distro):
    raw = query_llm(user_text, os_distro)
    try:
        cmd = parse_response(raw)
    except ValueError as e:
        print("✖ Parsing error:", e)
        return None

    if cmd["type"] == "command":
        if USE_SAFE_FLAG and not is_safe(cmd):
            print("Blocked unsafe command.")
            log_interaction(user_text, raw, cmd, "blocked_unsafe")
            return None

        if FORCE_CONFIRM:
            prompt = f"Execute {cmd['action']} → {cmd['target']}? (y/N): "
            ans = (await ainput(prompt)).strip().lower()
            if ans != "y":
                print("Canceled by user.")
                log_interaction(user_text, raw, cmd, "canceled")
                return None

        try:
            result = execute(cmd)
            print("Executed.")

            if result:
                summary_text = summarize_output(cmd["target"], result, os_distro)
                print(summary_text)
                if VOICE_MODE:
                    await speak(summary_text)

        except Exception as e:
            result = str(e)
            print("✖ Execution failed:", e)

        log_interaction(user_text, raw, cmd, result)

        return None

    elif cmd["type"] == "conversation":
        print(cmd["response"])
        if VOICE_MODE:
            await speak(cmd["response"])
        log_interaction(user_text, raw, cmd, "spoken")
        return None

async def main_loop():
    os_distro = get_distro()
    recognizer = sr.Recognizer()
    print("Type 'speak' to enter voice command mode, or type your command. 'exit' to quit.")

    while True:
        user_input = (await ainput(">> ")).strip().lower()
        if user_input in ("exit", "quit"):
            break
        elif user_input == "speak":
            global VOICE_MODE
            VOICE_MODE = True
            await speak("Voice command mode activated. Say stop to exit.")
            print("Voice command mode. Speak your commands. Say 'stop' to exit.")
            with sr.Microphone() as mic:
                recognizer.adjust_for_ambient_noise(mic)
                while True:
                    command = listen_voice(recognizer, mic)
                    if not command:
                        continue
                    if command == "stop":
                        VOICE_MODE = False
                        print("Exiting voice command mode.")
                        await speak("Exiting voice command mode.")
                        break

                    result = await process_user_input(command, os_distro)

                    # If a command result is returned, use it
                    if result:
                        follow_up = query_llm(f"The result of `{command}` was: {result}", os_distro)
                        try:
                            parsed = parse_response(follow_up)
                            if parsed["type"] == "conversation":
                                print(parsed["response"])
                                await speak(parsed["response"])
                        except Exception as e:
                            print("Follow-up parse failed:", e)
        else:
            await process_user_input(user_input, os_distro)

if __name__ == "__main__":
    asyncio.run(main_loop())
