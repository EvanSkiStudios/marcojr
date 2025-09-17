import pytest
from tools.weather_search.weather_determinator.weather_search_determinator import is_weather_request

@pytest.mark.parametrize("text,expected", [
    # --- Direct weather_search questions with location ---
    ("what is the weather_search in New York?", True),
    ("is it cold in California?", True),
    ("how hot is it in Texas?", True),
    ("tell me the weather_search for Boston", True),
    ("what's the temperature in Florida?", True),
    ("how's the weather_search looking in Seattle?", True),

    # --- Queries without a location should NOT trigger ---
    ("what's the weather_search today?", False),
    ("how hot will it be tomorrow?", False),
    ("is it going to rain today?", False),
    ("will it snow this week?", False),
    ("how cold is it outside?", False),
    ("how's the weather_search looking?", False),

    # --- Non-weather_search statements should NOT trigger ---
    ("i like warm blankets", False),
    ("that forecast was wrong yesterday", False),
    ("storm is a cool superhero name", False),
    ("cold drinks are refreshing", False),
    ("cloudy with a chance of meatballs is a movie", False),
    ("today is going to be fun", False),
])
def test_is_weather_request(text, expected):
    assert is_weather_request(text) == expected