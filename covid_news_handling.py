from core \
    import UpdateAction, add_update, remove_update, blacklist_article

import datetime
import requests
import json

def news_API_request(covid_terms="Covid COVID-19 coronavirus") -> dict:
    """Retrieves COVID news from the News API. Note: API usage is limited to 100 requests per day."""
    #Open the config file to get the API key.
    with open("data/config.json", "r") as f:
        json_file = json.load(f)
        api_key = json_file["api_key"]

    #Get and extract request data from newsapi.org
    api_exhausted = False
    request = requests.get(fr"https://newsapi.org/v2/everything?q={covid_terms}&sortBy=popularity&from={get_date(-7)}&apiKey={api_key}").json()
    if request["status"] == "error":
        if request["code"] == "rateLimited":
            data = None
            api_exhausted = True
    else:
        data = [{"title": news_article["title"], "content": news_article["url"]}
                for news_article in request["articles"]]

    #Handle blacklisting
    blacklisted_found = False
    for blacklisted_article in json_file["blacklisted_articles"]:
        if all([d["content"] != blacklisted_article for d in data]): #If the URL doesn't match any of the URLs of the news articles requested...
            continue
        else:
            blacklisted_found = True
            break

    if blacklisted_found:
        print("YES1")   
        for article in data[:]: #Iterating over and deleting from the same object causes unexpected behaviour so a new list is created, duplicating data.
            if article["content"] in json_file["blacklisted_articles"]: #If the URL matches one or more of the URLs in the news articles requested...
                print(article["content"])
                data.remove(article)

    #Return the correctly modified data and whether the API has been exhausted for the day.
    return data, api_exhausted

def update_news(update_name:str, update_interval:float=300, update_instantly:bool=True) -> None:
    """Base function for creating repetitive news updates via core.add_update().
    Can be updated less frequently than COVID statistics, as only 100 daily requests are permitted."""
    if update_instantly:
        current_data["news_articles"], current_data["api_exhausted"] = news_API_request()
    add_update(update_name, update_interval, [UpdateAction.NEWS_UPDATE_REQUEST, UpdateAction.REPETITIVE_REQUEST, UpdateAction.TIMED_REQUEST])

#print(news_API_request().json())