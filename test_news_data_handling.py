from covid_news_handling import news_API_request
from covid_news_handling import update_news

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
