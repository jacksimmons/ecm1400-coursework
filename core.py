"""Module which provides core functionality required by both
covid_data_handler and covid_news_handling."""

import datetime
import logging
from enum import IntEnum
import json

from functools import partial
open_utf8 = partial(open, encoding='UTF-8')

###Classes
class UpdateAction(IntEnum):
    """An enum class to allow the representation of different actions by discrete integers."""
    REPETITIVE_REQUEST      = 0
    TIMED_REQUEST           = 1

###Functions
def add_update(name:str, interval:float, update_type:str, actions:list) -> None:
    """Reformats and adds an update to config.json."""
    global current_data

    repetitive = False
    content = f"Update {update_type}" #String detailing the update
    if UpdateAction.REPETITIVE_REQUEST in actions:
        content += ", Repetitive"
        repetitive = True
    if UpdateAction.TIMED_REQUEST in actions:
        #Note: All requests must be timed otherwise they won't happen.
        content += f", Interval (in seconds): {str(interval)}"

    #Create the update
    new_update = {"title":name, "interval": interval, "content":content, "repetitive":repetitive}

    #open_utf8 config file and load the data
    with open_utf8("data/config.json", "r") as file:
        json_file = json.load(file)

    json_file[f"{update_type}_updates"].append(new_update)

    with open_utf8("data/config.json", "w") as file:
        json.dump(json_file, file, indent=4)

    current_data = json_file

def add_update_with_checks(update_name:str, update_interval:float, update_type:str, actions:list):
    """Uses add_update, but applies checks before doing so, outputting any issues to the log."""
    error_msg = ""
    #Check if the news update has a valid name
    if isinstance(update_name, str) and update_name != "":
        if update_name not in [upd["title"] for upd in current_data[f"{update_type}_updates"]]:
            add_update(update_name, update_interval, update_type, actions)
        else:
            error_msg = "Update with the same name already exists."
    else:
        error_msg = "Invalid update name."

    if error_msg != "":
        logging.warning(error_msg)
        with open_utf8("data/config.json", "r") as file:
            data = json.load(file)
        data["name_err"] = error_msg
        with open_utf8("data/config.json", "w") as file:
            json.dump(data, file, indent=4)
        return True #Error
    return False #No error

def remove_update(name:str, update_type:str) -> None:
    """Removes an update by name lookup."""
    global current_data

    #Load the config file so that we can edit it
    with open_utf8("data/config.json", "r") as file:
        json_file = json.load(file)

    for update in json_file[f"{update_type}_updates"]:
        if update["title"] == name:
            json_file[f"{update_type}_updates"].remove(update)
            break

    #Dump the edited dictionary, overwriting the original.
    with open_utf8("data/config.json", "w") as file:
        json.dump(json_file, file, indent=4)

    current_data = json_file

def get_date(offset:int=0) -> str:
    """Returns the date + the offset in YYYY-MM-DD (ISO 8601) format."""
    return (datetime.datetime.today() + datetime.timedelta(days=offset)).isoformat()

def get_data_from_file() -> dict:
    """Gets the current data from config.json and returns it."""
    with open_utf8("data/config.json", "r") as file:
        data = json.load(file)
    data["updates"] = data["covid_updates"] + data["news_updates"]
    return data

###Logging
#0-9: NotSet, 10-19: Debug, 20-29: Info, 30-39: Warn, 40-49: Error, 50+: Critical
def logging_setup():
    """Sets up logging for all modules with logging imported."""
    logging.basicConfig(format="%(asctime)s %(message)s",
                        level=logging.DEBUG,
                        filename="data/log.log",
                        filemode="a")
    logging.debug("\bLOGGING STARTUP\b")
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.ERROR)

###Globals
current_data = get_data_from_file()
updates_scheduled = []
