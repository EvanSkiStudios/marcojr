import os

import requests
from dotenv import load_dotenv

from tools.weather_search.state_capitals import get_capital

# Load Env
load_dotenv()

HEADERS = {
    "User-Agent": os.getenv("USER_AGENT")
}
BASE_URL = "https://api.weather.gov"


def geocode_city(session: requests.Session, city: str):
    """Get latitude/longitude for a city using OpenStreetMap Nominatim."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city, "format": "json", "limit": 1}
    resp = session.get(url, params=params, headers={"User-Agent": "city-geocoder"})
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise ValueError(f"Could not geocode city: {city}")
    city_name, state = extract_city_state(results[0]["display_name"])
    return float(results[0]["lat"]), float(results[0]["lon"]), city_name, state


def extract_city_state(display_name: str):
    # Split on commas, strip extra whitespace
    parts = [part.strip() for part in display_name.split(",")]
    if len(parts) < 3:
        raise ValueError(f"Unexpected format: '{display_name}'")
    city = parts[0]
    state = parts[-2]  # usually before country
    return city, state


def get_current_forecast(session: requests.Session, lat, lon):
    points_url = f"{BASE_URL}/points/{lat},{lon}"
    resp = session.get(points_url, headers=HEADERS)
    resp.raise_for_status()
    point_data = resp.json()

    forecast_url = point_data["properties"]["forecast"]

    forecast_resp = session.get(forecast_url, headers=HEADERS)
    forecast_resp.raise_for_status()
    forecast_data = forecast_resp.json()

    return forecast_data["properties"]["periods"][0]


def get_weather(city="", state=""):
    if not city:
        city = get_capital(state)

    with requests.Session() as session:
        lat, lon, city, state = geocode_city(session, city + ", " + state)
        current = get_current_forecast(session, lat, lon)
        return {
            "location": f"{city}, {state}",
            "summary": f"{current['name']}: {current['temperature']} {current['temperatureUnit']}, {current['shortForecast']}",
            "details": current["detailedForecast"],
        }


def slash_get_weather(city="", state=""):
    if not city:
        city = get_capital(state)

    with requests.Session() as session:
        lat, lon, city, state = geocode_city(session, city + ", " + state)
        current = get_current_forecast(session, lat, lon)
        return (f"""
The current weather in {city}, {state},
{current['name']}:
{current['temperature']} {current['temperatureUnit']},
{current["detailedForecast"]}
        """)


def main():
    city = "orlando"
    info = get_weather(city, "FL")
    print(info)


if __name__ == "__main__":
    main()
