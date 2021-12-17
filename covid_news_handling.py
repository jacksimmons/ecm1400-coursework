"""Module for handling COVID news updates."""

import requests

from core import (
    UpdateAction,
    get_data_from_file,
    write_data_to_file,
    add_update_with_checks,
    current_data,
    LOGGER)

#Globals
api_exhausted = False

def blacklist_article(article:dict) -> None:#
    """Removes and blacklists an article by URL lookup."""
    global current_data

    data = get_data_from_file()
    if article["content"] not in data["blacklisted_articles"]:
        #In case this procedure is used outside of the website.
        data["blacklisted_articles"].append(article["content"])
        data["news_articles"].remove(article)
        write_data_to_file(data)
        current_data = data

def news_API_request(covid_terms="Covid COVID-19 coronavirus") -> dict:#
    """Retrieves COVID news from the News API. Note: API usage is limited to 100 requests per
day."""
    global api_exhausted

    #Get and extract request data from newsapi.org
    api_exhausted = False
    request = requests.get(fr"""https://newsapi.org/v2/everything?q={covid_terms}&sortBy=
publishedAt&apiKey={current_data['api_key']}""").json()
    if request["status"] == "error":
        if request["code"] == "rateLimited":
            data = None
            api_exhausted = True
    else:
        #Create an interable for relevant parts of the data.
        data = [{"title": news_article["title"], "content": news_article["url"]}
                for news_article in request["articles"]]

    #Handle blacklisting
    blacklisted_found = False
    for blacklisted_article in current_data["blacklisted_articles"]:
        if all(item["content"] != blacklisted_article for item in data):
            #If the URL doesn't match any of the URLs of the news articles requested...
            continue
        #else...
        blacklisted_found = True
        break

    if blacklisted_found:
        for article in data[:]:
            #Create a new list to avoid editing the list being iterated
            if article["content"] in current_data["blacklisted_articles"]:
                #If the URL matches one or more of the URLs in the news articles requested...
                data.remove(article)

    #Return the correctly modified data and whether the API has been exhausted for the day.
    return data

def update_news_request(update:dict) -> None:#
    """Uses news_API_request to update the news and update config.json and the relevant data
structures to reflect this."""
    global current_data

    print("Covid News Request from " + update["title"])
    LOGGER.info("Covid News Request from %s", update["title"])

    news_articles = news_API_request()

    json_file = get_data_from_file()
    json_file["news_articles"] = news_articles
    write_data_to_file(json_file)

    current_data = json_file

def update_news(update_name:str, update_interval:float=300) -> None:#
    """Base function for creating repetitive news updates via add_update().
Cannot be done as freely as COVID statistics, as only 100 daily requests are
permitted."""
    try:
        update_interval = float(update_interval)
        cont = update_interval >= 0
    except ValueError: #interval invalid
        cont = False
    if cont:
        actions = [UpdateAction.REPETITIVE_REQUEST, UpdateAction.TIMED_REQUEST]
        add_update_with_checks(update_name, update_interval, "news", actions)
    else:
        LOGGER.error("[update_news] update_interval must be a float >= 0.")
