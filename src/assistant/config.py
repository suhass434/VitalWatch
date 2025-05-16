import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
# Load key
API_KEY = os.getenv("GEMINI_API_KEY")

# Whitelists
ACTION_WHITELIST = {"open_file", "shutdown", "run_command"}
FILE_WHITELIST = {
    "/usr/bin/code",
    str(Path.home() / "Downloads"),
    # add any others here
}

# If you want to keep a “safe” flag from the LLM
USE_SAFE_FLAG = True  

# Always ask for confirmation:
FORCE_CONFIRM = True