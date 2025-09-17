import re
import json
import os

# Load patterns from JSON for flexibility
_patterns_file = os.path.join(os.path.dirname(__file__), "weather_rex_patterns.json")

with open(_patterns_file, "r", encoding="utf-8") as f:
    WEATHER_PATTERNS = json.load(f)

PATTERNS = [re.compile(p, re.I) for p in WEATHER_PATTERNS]


def is_weather_request(text: str) -> bool:
    text = (text or "").strip()
    if not text:
        return False
    for pat in PATTERNS:
        if pat.search(text):
            return True
    return False
