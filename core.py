"""Module which provides core functionality required by both
covid_data_handler and covid_news_handling."""

import datetime
import logging
from enum import IntEnum
import json
import os

from functools import partial
open_utf8 = partial(open, encoding='UTF-8')

###Globals
current_data = {}
LOGGER = logging.getLogger()
adding_update = False

###Classes
class UpdateAction(IntEnum):
    """An enum class to allow the representation of different actions by discrete integers."""
    REPETITIVE_REQUEST      = 0
    TIMED_REQUEST           = 1

###Functions
def get_date(offset:int=0) -> str:#
    """Returns the date + the offset in YYYY-MM-DD (ISO 8601) format."""
    return (datetime.datetime.today() + datetime.timedelta(days=offset)).isoformat()

def get_data_from_file() -> dict:#
    """Gets the current data from config.json and returns it."""
    try:
        if os.stat("data/config.json").st_size != 0:
            with open_utf8("data/config.json", "r") as file:
                data = json.load(file)
            data["updates"] = data["covid_updates"] + data["news_updates"]
            return data
        #else...
        LOGGER.error("Read: The config file is empty. Reading aborted.")
        return current_data
    except PermissionError:
        #Recursively call the function until it is not in use by an update.
        #The file being in use by an update is rare.
        LOGGER.error("Read: config.json is in use [perms]. Trying again...")
        return get_data_from_file()
    except json.JSONDecodeError:
        LOGGER.critical("Read: config.json is in use [empty]. Aborting...")
        return current_data

def write_data_to_file(data:dict) -> None:#
    """Puts the supplied data into config.json."""
    try:
        with open_utf8("data/config.json", "w") as file:
            json.dump(data, file, indent=4)
    except PermissionError:
        #Recursively call the function until it is not in use by an update.
        #The file being in use by an update is rare.
        LOGGER.error("Write: config.json already in use. Trying again...")
        write_data_to_file(data)

def add_update(name:str, interval:float, update_type:str, actions:list) -> None:#
    """Reformats and adds an update to config.json."""
    global adding_update
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
    json_file = current_data
    json_file[f"{update_type}_updates"].append(new_update)
    write_data_to_file(json_file)

    current_data = json_file

    #Make it so other updates can be added now
    adding_update = False

def add_update_with_checks(update_name:str, update_interval:float, update_type:str,
                           actions:list[UpdateAction]) -> bool:#
    """Uses add_update, but applies checks before doing so, outputting any issues to the log."""
    global adding_update
    global current_data

    current_data = get_data_from_file()

    if not adding_update:
        adding_update = True

        error_msg = ""
        #Check if the news update has a valid name
        if isinstance(update_name, str) and update_name != "":
            if update_name not in [upd["title"] for upd in current_data[f"{update_type}_updates"]]:
                add_update(update_name, update_interval, update_type, actions)
            else:
                print("lol")
                error_msg = "Update with the same name already exists."
        else:
            print("HI")
            error_msg = "Invalid update name."

        if error_msg != "":
            LOGGER.warning(error_msg)
            data = current_data
            data["name_err"] = error_msg
            write_data_to_file(data)
            return True #Error
        return False #No error
    error_msg = "You can't add an update multiple times."
    data = current_data
    data["name_err"] = error_msg
    write_data_to_file(data)
    return True #Error - already adding an update.

def remove_update(name:str, update_type:str) -> None:
    """Removes an update by name lookup."""
    global current_data

    #Load the config file so that we can edit it
    json_file = get_data_from_file()
    spec_updates = json_file[f"{update_type}_updates"] #Specified updates
    name_found = False
    the_update = {}
    if not spec_updates: # == []
        LOGGER.warning("""Cannot remove this %s update,
as there are no updates of that type.""", update_type)
    else:
        for index, update in enumerate(spec_updates):
            if update["title"] == name:
                #Don't remove from the list being iterated upon
                name_found = True
                the_update = update
                json_file[f"{update_type}_updates"].remove(the_update)
                json_file["updates"].remove(the_update)
            else:
                #If the name has not been found and this update is not a match...
                if index == len(spec_updates) - 1:
                    #If this update is the last one...
                    LOGGER.warning("No %s update was found with that name.", update_type)

    current_data = json_file

    if name_found and the_update in current_data["updates_scheduled"]:
        current_data[f"{update_type}_updates_scheduled"].remove(the_update)
        current_data["updates_scheduled"].remove(the_update)

    write_data_to_file(current_data)

###Logging
#0-9: NotSet, 10-19: Debug, 20-29: Info, 30-39: Warn, 40-49: Error, 50+: Critical
def logging_setup() -> logging.Logger:
    """Sets up logging for all modules with logging imported."""
    global current_data

    current_data = get_data_from_file()

    logging.basicConfig(format="%(asctime)s %(message)s",
                        level=current_data["log_level"],
                        filename="data/log.log",
                        filemode="a")
    logging.info("\bLOGGING STARTUP\b")
    logger = logging.getLogger("Logger")
    logger.setLevel(current_data["log_level"])
    return logger

current_data = get_data_from_file()
LOGGER = logging_setup()
