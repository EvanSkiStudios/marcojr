import pytest
from tools.web_search.search_determinator.internet_search_determinator import is_search_request

import re
import json
from pathlib import Path

# Adjust path: go one folder up from the test file
_patterns_file = Path(__file__).parent.parent / "search_patterns.json"

# validate that all regex patterns compile
with open(_patterns_file, "r", encoding="utf-8") as f:
    SEARCH_PATTERNS = json.load(f)

for i, pat in enumerate(SEARCH_PATTERNS, 1):
    try:
        re.compile(pat)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern #{i}: {pat}\n{e}")


@pytest.mark.parametrize("text,expected", [
    # --- Direct commands ---
    ("search the web for apples", True),
    ("google for apples", True),
    ("look up some apples", True),
    ("show me Wikipedia for apples", True),
    ("check the internet for apples", True),
    ("search for apples", True),

    # --- Polite / indirect phrasing ---
    ("please find me some apples", True),
    ("could you look up apples for me", True),
    ("would you google apples", True),
    ("please search apples", True),

    # --- Question-style requests ---
    ("where can I find info on apples online?", True),
    ("how do I look up apples?", True),
    ("can you check the web for apples?", True),
    ("is there a wikipedia page for apples?", True),
    ("are there any websites about apples?", True),
    ("do you know if there is a wiki page for apples?", True),

    # --- Not searches (should be False) ---
    ("whats your favorite apple", False),
    ("i like google as a company", False),
    ("wikipedia is useful", False),
    ("i found apples in the store", False),
    ("google is a big company", False),
    ("reading wikipedia articles is fun", False),

    # --- Negative test Cases ---
    ("google headquarters is in california", False),
    ("google was founded in 1998", False),
    ("reading a wikipedia article yesterday", False),
    ("wikipedia is a non-profit organization", False),
    ("the web is vast and complex", False),
])
def test_is_search_request(text, expected):
    assert is_search_request(text) == expected
