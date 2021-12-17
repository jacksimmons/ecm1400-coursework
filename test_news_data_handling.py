from core import get_data_from_file
from core import write_data_to_file

from covid_news_handling import news_API_request
from covid_news_handling import update_news

from covid_news_handling import blacklist_article
from covid_news_handling import update_news_request

def test_news_API_request():
    #Note that if the news articles in NewsAPI update in between the function calls this may fail.
    assert news_API_request()
    assert news_API_request('Covid COVID-19 coronavirus') == news_API_request()

def test_update_news():
    #Normal
    update_news("test")
    #Boundary
    update_news(update_name="test 2", update_interval=0)
    #Erroneous
    update_news(update_interval=-1, update_name=1)
    update_news(update_interval=1, update_name=1)
    update_news(update_interval="a", update_name="test 3")
    update_news(update_interval=1, update_name="test") # Duplicate name error

test_news_API_request()
test_update_news()

#My Tests
def test_blacklist_article():
    #Visual test - involves looking in config.json and at the website to confirm.
    data = get_data_from_file()
    data["news_articles"].append({"content": "www.google.com", "title": "Google"})
    write_data_to_file(data)
    #Content is the URL of the article
    blacklist_article({"content": "www.google.com", "title": "Google"})
    #The best way to test this function is to see whether the blacklisted article appears in future
    #news updates on the website.
    assert "www.google.com" in get_data_from_file()["blacklisted_articles"]
    assert "www.google.com" not in get_data_from_file()["news_articles"]

def test_update_news_request():
    #Visual test - involves looking in config.json and at the website to confirm.
    update = {"title": "test",
         "interval": 0.0,
         "content":"Update news, Repetitive, Interval (in seconds): 0.0",
         "repetitive": False}
    update_news_request(update)
    print(get_data_from_file()["news_articles"])
    #The data will be placed into config.json and onto the website

test_blacklist_article()
test_update_news_request()
