from tools.web_search.search_determinator.internet_search_determinator import is_search_request
from tools.weather_search.weather_determinator.weather_search_determinator import is_weather_request


def classify_request(text: str) -> str:
    if is_weather_request(text):
        return "weather_search"
    elif is_search_request(text):
        return "search"
    else:
        return "conversation"
