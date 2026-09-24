import os
from dotenv import load_dotenv
import requests

from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

load_dotenv()

# Tool to give out AI Agent capability to search through the internet
web_search_tool = DuckDuckGoSearchRun()

# Tool to get live weather update
@tool
def get_weather_update(city: str) -> str:
    """
    This tool fetches the current weather data for a given city
    """
    url = f'https://api.weatherstack.com/current?access_key={os.getenv("WEATHERSTACK_API_KEY")}&query={city}'

    response = requests.get(url)

    return response.json()

if __name__ == "__main__":
    response = web_search_tool.invoke("LA Olympics 2028") # First try this, then comment it out
    print(response)

    response = get_weather_update.invoke({"city": "Hyderabad"}) # Then try this
    print(response)