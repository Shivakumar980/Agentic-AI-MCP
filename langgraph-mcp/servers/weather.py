import asyncio
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather")

# Geocoding API to convert location to coordinates
GEOCODING_API = "https://geocoding-api.open-meteo.com/v1/search"
# Weather API for current conditions
WEATHER_API = "https://api.open-meteo.com/v1/forecast"

@mcp.tool()
async def get_weather(location: str) -> str:
    """Get current weather for the specified location."""
    try:
        async with httpx.AsyncClient() as client:
            # First, get coordinates for the location
            params = {
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            response = await client.get(GEOCODING_API, params=params)
            geo_data = response.json()
            
            if not geo_data.get("results"):
                return f"Sorry, I couldn't find the location: {location}"
            
            # Get first result
            location_data = geo_data["results"][0]
            lat = location_data["latitude"]
            lon = location_data["longitude"]
            name = location_data["name"]
            
            # Now get the weather data
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "timezone": "auto"
            }
            response = await client.get(WEATHER_API, params=params)
            weather_data = response.json()
            
            if "current" not in weather_data:
                return f"Sorry, I couldn't retrieve weather data for {name}"
            
            # Get current conditions
            current = weather_data["current"]
            temp = current["temperature_2m"]
            temp_unit = weather_data["current_units"]["temperature_2m"]
            
            # Map weather code to description
            # Basic mapping of weather codes to descriptions
            weather_codes = {
                0: "Clear sky",
                1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Fog", 48: "Depositing rime fog",
                51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
                80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
            }
            
            weather_code = current["weather_code"]
            condition = weather_codes.get(weather_code, f"Unknown (code {weather_code})")
            
            return f"The current weather in {name} is {condition} with a temperature of {temp}{temp_unit}."
    except Exception as e:
        return f"Sorry, I couldn't retrieve the weather for {location}. Error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="sse")