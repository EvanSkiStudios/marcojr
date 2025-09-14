import aiohttp
import asyncio

HEADERS = {
    "User-Agent": "SAM (https://github.com/EvanSkiStudios/sam_ai_assistant; EvanskiStudios@gmail.com)"
}
BASE_URL = "https://api.weather.gov"


async def geocode_city(session: aiohttp.ClientSession, city: str):
    """Get latitude/longitude for a city using OpenStreetMap Nominatim."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city, "format": "json", "limit": 1}
    async with session.get(url, params=params, headers={"User-Agent": "city-geocoder"}) as resp:
        resp.raise_for_status()
        results = await resp.json()
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


async def get_current_forecast(session: aiohttp.ClientSession, lat, lon):
    points_url = f"{BASE_URL}/points/{lat},{lon}"
    async with session.get(points_url, headers=HEADERS) as resp:
        resp.raise_for_status()
        point_data = await resp.json()

    forecast_url = point_data["properties"]["forecast"]

    async with session.get(forecast_url, headers=HEADERS) as forecast_resp:
        forecast_resp.raise_for_status()
        forecast_data = await forecast_resp.json()

    return forecast_data["properties"]["periods"][0]


async def get_weather(city, state=""):
    async with aiohttp.ClientSession() as session:
        lat, lon, city, state = await geocode_city(session, city+", "+state)
        current = await get_current_forecast(session, lat, lon)
        output = (
            f"{city}, {state}",
            f"{current['name']}: {current['temperature']} {current['temperatureUnit']}, {current['shortForecast']}",
            current["detailedForecast"]
        )
        return output


async def main():
    city = "orlando"
    info = await get_weather(city, "FL")
    print(info)


if __name__ == "__main__":
    asyncio.run(main())

