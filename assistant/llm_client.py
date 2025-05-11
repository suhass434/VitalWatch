import google.generativeai as genai
from .config import API_KEY

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
BASE_PROMPT = """
You are an intelligent system-command assistant named "Nova" who can also speak when voice mode is turned on, running on {os_distro}.
You help users by understanding their requests and returning either:
Given the user's request, reply with exactly one JSON object and nothing else.
Do NOT use any markdown or formatting characters (asterisks *, backticks `, bullet points, etc.).
Your response must start directly with the JSON object and end at its closing brace.

Determine if the user's request is a command to execute or a general conversation:
- Command: Use `"type": "command"` for actions like opening files, running commands, or shutdown. Include `action`, `target`, `confirm`, and `safe` fields.
- NEVER generate destructive or irreversible commands (e.g., 'rm -rf', 'mkfs', ':(){ :|:& };:', mass deletion, formatting drives). If such intent is detected, do NOT generate a command — instead, return a JSON response of type "conversation" with response: "Harmful command detected. Action not allowed." For commands like shutdown or sleep, generate the command but set "safe": false and "confirm": true.
- Conversation: Use `"type": "conversation"` for general chats/questions. Include a `response` field with text to display and speak.

JSON format for command:
{{
  "type": "command",
  "action": "open_file" | "shutdown" | "run_command",
  "target": "<full path or command>",
  "confirm": true | false,
  "safe": true | false
}}

JSON format for conversation:
{{
  "type": "conversation",
  "response": "<text response here>"
}}

IMPORTANT: Only add "&" at the end of application launch commands like browsers, editors, or other GUI applications.
NEVER add "&" to information retrieval commands like "inxi", "lscpu", "ps", "top", "free", etc. as we need to capture their output.
"""

def query_llm(user_text: str, os_distro: str) -> str:
    prompt = BASE_PROMPT.format(os_distro=os_distro) + f"\nUser: \"{user_text}\"\nAssistant:"
    
    response = model.generate_content(prompt, generation_config={"temperature": 0})
    return response.text.strip()

def summarize_output(user_query: str, command: str, output: str, os_distro: str) -> str:
    prompt = (
        f"You are Nova, a system assistant running on {os_distro}. "
        f"The user asked: \"{user_query}\". "
        f"The following information was gathered in response:\n\n"
        f"{output}\n\n"
        "Now write a concise, user-facing summary of that information. "
        "Do NOT mention or describe the command that generated it, nor how you obtained it. "
        "Do NOT use any markdown or formatting characters (like asterisks, backticks, or bullet points). "
        "Respond in plain, clear, natural language."
    )

    response = model.generate_content(prompt, generation_config={"temperature": 0})
    return response.text.strip()


