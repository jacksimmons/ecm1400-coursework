from core \
    import UpdateAction, add_update, remove_update, blacklist_article

import datetime
import requests
import json
import logging
import requests

def update_news_request() -> None:
    """Uses news_API_request to update the news and update config.json and the relevant data structures to reflect this."""
    current_data["news_articles"], current_data["api_exhausted"] = news_API_request()
    with open("data/config.json", "r") as f:
        json_file = json.load(f)
    json_file["news_articles"] = current_data["news_articles"]
    with open("data/config.json", "w") as f:
       json.dump(json_file, f, indent=4)

def update_news(update_name:str, update_interval:float=300) -> None:#
    """Base function for creating repetitive news updates via core.add_update().
    Can be updated less frequently than COVID statistics, as only 100 daily requests are permitted."""
    try:
        update_interval = float(update_interval)
        cont = update_interval >= 0
    except ValueError:
        cont = False
    if cont:
        core.add_update_with_checks(update_name, update_interval, core.UpdateAction.NEWS_UPDATE_REQUEST)
    else:
        logging.error("[update_news] update_interval must be a float >= 0.")

def news_API_request(covid_terms="Covid COVID-19 coronavirus") -> dict:
    """Retrieves COVID news from the News API. Note: API usage is limited to 100 requests per day."""
    #Unfortunately with the method I have used, this function needs to be in here since the startup code below uses it, and that in turn must be in a different file
    #to covid_news_handling to prevent a circular import.

    #Open the config file to get the API key.
    with open("data/config.json", "r") as f:
        json_file = json.load(f)
        api_key = json_file["api_key"]

    #Get and extract request data from newsapi.org
    api_exhausted = False
    request = requests.get(fr"https://newsapi.org/v2/everything?q={covid_terms}&sortBy=popularity&from={core.get_date(-7)}&apiKey={api_key}").json()
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