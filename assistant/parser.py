import json
from jsonschema import validate, ValidationError

SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"enum": ["command", "conversation"]}
    },
    "required": ["type"],
    "oneOf": [
        {
            "properties": {
                "type": {"const": "command"},
                "action": {"enum": ["open_file", "shutdown", "run_command"]},
                "target": {"type": "string"},
                "confirm": {"type": "boolean"},
                "safe": {"type": "boolean"}
            },
            "required": ["action", "target", "confirm", "safe"],
            "additionalProperties": False  # Restrict to command-specific fields
        },
        {
            "properties": {
                "type": {"const": "conversation"},
                "response": {"type": "string"}
            },
            "required": ["response"],
            "additionalProperties": False  # Restrict to conversation-specific fields
        }
    ]
}

def parse_response(raw: str) -> dict:
    try:
        data = json.loads(raw)
        validate(instance=data, schema=SCHEMA)
        return data
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"Invalid LLM response: {e}")
