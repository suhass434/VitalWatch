import google.generativeai as genai
from .config import API_KEY

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
BASE_PROMPT = """
You are an intelligent system-command assistant named "Nova" who can also speak, running on {os_distro}.
You help users by understanding their requests and returning either:
Given the user's request, reply with exactly one JSON object and nothing else.
Do NOT include code block formatting like triple backticks (```).
Your response must start directly with the JSON object and end at its closing brace.

Determine if the user's request is a command to execute or a general conversation:
- Command: Use `"type": "command"` for actions like opening files, running commands, or shutdown. Include `action`, `target`, `confirm`, and `safe` fields.
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

For commands like opening applications, ensure they are executed in a "new terminal window", (ex: by adding an "&" at the end).
"""

def query_llm(user_text: str, os_distro: str) -> str:
    prompt = BASE_PROMPT.format(os_distro=os_distro) + f"\nUser: \"{user_text}\"\nAssistant:"
    
    response = model.generate_content(prompt, generation_config={"temperature": 0})
    return response.text.strip()

def summarize_output(command: str, output: str, os_distro: str) -> str:
    prompt = (
        f"You are Nova, a system assistant on {os_distro}. "
        f"A command was run:\n\n{command}\n\n"
        f"Its output was:\n\n{output}\n\n"
        "Summarize the output clearly and concisely. Do not greet the user. Do not start with 'Hello' or similar. "
        "Just give a short and direct summary of the output."
    )
    
    response = model.generate_content(prompt, generation_config={"temperature": 0})
    return response.text.strip()
