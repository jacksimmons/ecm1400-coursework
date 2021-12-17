import json
import time

from core import get_date
from core import get_data_from_file
from core import write_data_to_file
from core import add_update_with_checks, UpdateAction
from core import remove_update
from core import logging_setup

def test_get_date():
    print(get_date())

def test_get_data_from_file():
    with open("data/config.json", "r") as f:
        data = json.load(f)
    data["updates"] = data["covid_updates"] + data["news_updates"]
    assert get_data_from_file() == data

def test_write_data_to_file():
    file = get_data_from_file()
    file["Test"] = "Content"
    write_data_to_file(file)
    assert "Test" in get_data_from_file()

def test_add_update_with_checks():
    #This is also a test for add_update, as add_update_with_checks is the only
    #code to call add_update.
    data = get_data_from_file()
    data["covid_updates"] = []
    data["covid_updates_scheduled"] = []
    data["news_updates"] = []
    data["news_updates_scheduled"] = []
    data["updates"] = []
    data["updates_scheduled"] = []
    write_data_to_file(data)

    #Normal
    add_update_with_checks("Test", 0, "covid", [UpdateAction.TIMED_REQUEST, UpdateAction.REPETITIVE_REQUEST])
    add_update_with_checks("Test", 0, "news", [UpdateAction.TIMED_REQUEST, UpdateAction.REPETITIVE_REQUEST])

    #Erroneous
    assert add_update_with_checks("", 0, "covid", [UpdateAction.TIMED_REQUEST])
    assert add_update_with_checks("Test", 0, "covid", [UpdateAction.TIMED_REQUEST])

def test_remove_update():
    data = get_data_from_file()
    data["covid_updates"] = []
    data["covid_updates_scheduled"] = []
    data["news_updates"] = []
    data["news_updates_scheduled"] = []
    data["updates"] = []
    data["updates_scheduled"] = []
    write_data_to_file(data)

    add_update_with_checks("Test", 0, "covid", [UpdateAction.TIMED_REQUEST, UpdateAction.REPETITIVE_REQUEST])
    remove_update("Test", "covid")
    assert "Test" not in [update["title"] for update in get_data_from_file()["covid_updates"]]

    add_update_with_checks("Test", 0, "news", [UpdateAction.TIMED_REQUEST, UpdateAction.REPETITIVE_REQUEST])
    remove_update("Test", "news")
    assert "Test" not in [update["title"] for update in get_data_from_file()["news_updates"]]

def test_logging_setup():
    #Visual test, need to look in log.log
    data = get_data_from_file()
    data["log_level"] = 50
    write_data_to_file(data)
    LOGGER = logging_setup()
    assert LOGGER.level == 50
    #Note there will be no "LOGGING STARTUP" as info < 50.
    LOGGER.critical("This will be sent to the log.")
    LOGGER.log(49, "This will not be sent to the log.")

test_get_date()
test_get_data_from_file()
test_write_data_to_file()
test_add_update_with_checks()
test_remove_update()
test_logging_setup()

#Return log level to 30
data = get_data_from_file()
data["log_level"] = 30
write_data_to_file(data)