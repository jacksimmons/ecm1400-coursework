from covid_news_handling import news_API_request
from covid_news_handling import update_news

def test_news_API_request():
    assert news_API_request()
    assert news_API_request('Covid COVID-19 coronavirus') == news_API_request()

def test_update_news():
    #Normal
    #update_news("test")
    #Boundary
    #update_news(update_name="test 2", update_interval=0)
    #Erroneous
    #update_news(update_interval=-1, update_name=1)
    #update_news(update_interval=1, update_name=1)
    update_news(update_interval="a", update_name="test 3")

test_update_news()
