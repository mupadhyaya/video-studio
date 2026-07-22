import requests
from langchain_core.tools import tool

@tool
def get_weather_data(location: str) -> str:
    """
    Fetch real-time weather information for a specific city location.
    Use this tool when users ask about current weather or temperatures.
    """
    base_url = "https://api.weatherapi.com/v1/current.json"
    # Production implementation with mock response representing dynamic fetching
    # replace with actual API key and requests call in your live environments
    try:
        params = {"key": "YOUR_API_KEY", "q": location, "aqi": "no"}
        # response = requests.get(base_url, params=params, timeout=5)
        # data = response.json()
        
        # Simulated production response structure
        if location.lower() == "tokyo":
            return "Location: Tokyo, Temp: 22C, Condition: Sunny, Wind: 12km/h"
        else:
            return f"Location: {location}, Temp: 18C, Condition: Partly Cloudy"
    except Exception as e:
        return f"Error querying weather API: {str(e)}"