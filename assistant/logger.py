import logging

logging.basicConfig(
    filename="assistant/assistant.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def log_interaction(user_text, llm_raw, parsed, result):
    logging.info("USER: %s", user_text)
    logging.info("LLM_RAW: %s", llm_raw)
    logging.info("PARSED: %s", parsed)
    logging.info("RESULT: %s", result)
