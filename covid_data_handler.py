"""Module for handling COVID data updates."""
import csv
from typing import Union

from uk_covid19 import Cov19API

from core import (
    UpdateAction,
    get_data_from_file,
    write_data_to_file,
    add_update_with_checks,
    open_utf8,
    current_data,
    LOGGER)

def parse_csv_data(csv_filename:str) -> list[list[str]]:#
    """Parses CSV file data into a list of lists (rows) of data items,
each nested list representing a row in the file."""
    csv_data = []
    csv_current_row = []
    with open_utf8(csv_filename, "r") as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            csv_current_row = list(row)
            csv_data.append(csv_current_row)
    return csv_data

def process_covid_csv_data(covid_csv_data:list) -> list[int]:#
    """Processes parsed COVID-19 CSV data and returns important statistics."""
    #Check if other data is present first, then...
    #If cases data is present for a day and the 6 days before, then we can get weekly cases...
    #Otherwise, continue to the next iteration...
    #If the end of the loop is reached, return nothing ([]).
    skip_first_entry = get_data_from_file()["csv_skip_first_entry"]

    current_hospital_cases_obtained = False
    total_deaths_obtained = False
    last7days_cases_obtained = False
    last7days_cases = 0
    skipped_first_valid_entry = False

    for index, row in enumerate(covid_csv_data):
#Need to use hard coded logic for indices as each row is a list of the same format:
#areaCode,areaName,areaType,date,cumDailyNsoDeathsByDeathDate,hospitalCases,newCasesBySpecimenDate
        if not current_hospital_cases_obtained:
            try:
                current_hospital_cases = int(row[5])
                current_hospital_cases_obtained = True
            except ValueError: #Data missing (non-int-castable)
                LOGGER.warning("CSV: Hospital cases missing (non-int-castable).")

        if not total_deaths_obtained:
            try:
                total_deaths = int(row[4])
                total_deaths_obtained = True
            except ValueError: #Data missing (non-int-castable)
                LOGGER.warning("CSV: Deaths missing (non-int-castable).")

        if not last7days_cases_obtained:
            try:
                last7days_cases = int(row[6])

                if not skipped_first_valid_entry and skip_first_entry:
                    #This is the 27/10 data, which is incomplete on the cases data, so next entry.
                    #The very first entry (the column names) is caught by the try-except statement.
                    skipped_first_valid_entry = True
                    continue

                for day_index in range(index + 1, index + 7):
                    try:
                        last7days_cases += int(covid_csv_data[day_index][6])
                        last7days_cases_obtained = True
                    except ValueError: #The value is not an integer; missing data
                        last7days_cases = 0
                        last7days_cases_obtained = False
                        LOGGER.warning("CSV: Weekly cases data missing (non-int-castable).")

                if not last7days_cases_obtained:
                    #Reset the value as data was not found for every day in the week preceding it.
                    last7days_cases = 0
            except ValueError:
                LOGGER.warning("CSV: Daily cases data missing (non-int-castable).")

        if current_hospital_cases_obtained and total_deaths_obtained and last7days_cases_obtained:
            LOGGER.info("CSV processing succeeded.")
            return last7days_cases, current_hospital_cases, total_deaths

    LOGGER.error("CSV processing failed.")
    #No days were found for which all data was present
    return 0, 0, 0

def covid_API_hospital_cases_request(filters:list) -> Union[int, str]:#
    """Carries out a COVID API data request for hospital cases and returns the result."""
    hospital_api = Cov19API(filters=filters, structure={"hospitalCases":"hospitalCases"}).get_json()

    for update in hospital_api["data"]:
        if update["hospitalCases"] is not None:
            hospital_cases = update["hospitalCases"]
            break
        LOGGER.debug("API Data Missing: hospitalCases.")
    else: #No hospital stats available.
        hospital_cases = "N/A"
        LOGGER.warning("Important data is missing from the API: Hospital cases.")

    return hospital_cases

def covid_API_request(location:str="Exeter",
                      location_type:str="ltla") -> dict:#
    """Carries out a COVID API data request and returns the result. Note that in this context,
updates are each a day's worth of COVID data, not an update defined by the user."""
    filters = [
        f"areaType={location_type}",
        f"areaName={location}"]

    structure = {
        "date": "date",
        "cumDailyNsoDeathsByDeathDate": "cumDailyNsoDeathsByDeathDate",
        "newCasesByPublishDate": "newCasesByPublishDate"
    }
    if location_type != "nation":
        structure.pop("cumDailyNsoDeathsByDeathDate")

    api = Cov19API(
        filters=filters,
        structure=structure)

    updates = api.get_json() #Local variable

    most_recent_data = {}
    keys = list(structure.keys())

    exit_index = -1
    for update in updates["data"]:
        if all(update[key] is not None for key in keys):
            #If every key in the update has a non-None value...
            most_recent_data = update
            exit_index = updates["data"].index(update)
            break

    if most_recent_data == {}:
        LOGGER.critical("API Data Missing: ALL")
        #The entire update has failed; critical error. Occurs if no days have a full set of valid
        #data, which is incredibly unlikely.
        return {} #No full set of data was obtained, so exit here.

    ##Data: See structure
    most_recent_data["newCases7DaysByPublishDate"] = 0
    if len(updates["data"]) > exit_index + 7:
        #Add the new cases for the past week
        for item in updates["data"][exit_index : exit_index + 7]:
            if item["newCasesByPublishDate"] is not None:
                most_recent_data["newCases7DaysByPublishDate"] += item["newCasesByPublishDate"]
            else:
                LOGGER.warning("API Data Missing: New weekly cases (for one of the days).")

    else:
        most_recent_data["newCases7DaysByPublishDate"] = "N/A"
        LOGGER.error("API Data Missing: Cumulative infections from a week ago or older.")

    if location_type == "nation":
        most_recent_data["hospitalCases"] = covid_API_hospital_cases_request(filters)

    return most_recent_data

def schedule_covid_updates(update_name:str, update_interval:float) -> None:#
    """Base function for creating repetitive updates via add_update()."""
    try:
        update_interval = float(update_interval)
        cont = update_interval >= 0
    except ValueError: #interval not valid
        cont = False
    if cont:
        actions = [UpdateAction.REPETITIVE_REQUEST, UpdateAction.TIMED_REQUEST]
        add_update_with_checks(update_name, update_interval, "covid", actions)
    else:
        LOGGER.error("[schedule_covid_updates] update_interval must be a float >= 0.")

def covid_update_request(update:dict, local:str="Exeter", nation:str="England") -> None:#
    """Uses covid_API_request to update the main webpage for scheduled updates."""
    global current_data

    print("Covid Update Request from " + update["title"])
    LOGGER.info("Covid Update Request from %s", update["title"])

    local_data = covid_API_request(location=local, location_type="ltla")
    national_data = covid_API_request(location=nation, location_type="nation")

    json_file = get_data_from_file()
    json_file.update({
                    "location": local,
                    "nation_location": nation,
                    "local_7day_infections": local_data["newCases7DaysByPublishDate"],
                    "national_7day_infections": national_data["newCases7DaysByPublishDate"],
                    "hospital_cases": national_data["hospitalCases"],
                    "deaths_total": national_data["cumDailyNsoDeathsByDeathDate"]})
    write_data_to_file(json_file)

    current_data = json_file
