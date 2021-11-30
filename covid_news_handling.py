import requests
import json
import os
from requests.models import Response
print(os.getcwd())
news_articles = {}

def news_API_request(covid_terms="Covid COVID-19 coronavirus") -> Response:
    """Retrieves COVID news from the News API."""
    with open("data/config.json", "r") as f:
        json_file = json.load(f)
        api_key = json_file["api_key"]
    return requests.get(fr"https://newsapi.org/v2/everything?q={covid_terms}&sortBy=popularity&apiKey={api_key}")

print(news_API_request().json())

def update_news():
    """Uses news_API_request to update stored news."""
    news_articles = news_API_request()