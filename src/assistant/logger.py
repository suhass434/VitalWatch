import logging
import os
import sys

def get_resource_path(relative_path):
    """Get the absolute path to bundled files when using PyInstaller."""
    if getattr(sys, 'frozen', False):  # Running as a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

logging.basicConfig(
    filename=get_resource_path("src/assistant/assistant.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def log_interaction(user_text, llm_raw, parsed, result):
    logging.info("USER: %s", user_text)
    logging.info("LLM_RAW: %s", llm_raw)
    logging.info("PARSED: %s", parsed)
    logging.info("RESULT: %s", result)
