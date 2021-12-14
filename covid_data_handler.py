"""Module for handling COVID data updates."""
import csv
import logging
import json
from typing import Union

from uk_covid19 import Cov19API

from core import (
    UpdateAction,
    add_update_with_checks,
    open_utf8,
    current_data)

def parse_csv_data(csv_filename: str) -> list[list[str]]:#
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

def process_covid_csv_data(covid_csv_data: list) -> list[int]:#
    """Processes parsed COVID-19 CSV data and returns important statistics."""
    cnt = 7
    last_7_days_cases = 0
    skip_upto_incl = 2
    for row in covid_csv_data:
        if covid_csv_data.index(row) <= skip_upto_incl:
            #Skips the items with missing data. ! Need to make this more dynamic
            continue

        #Note: This won't give valid weekly readings if data is regularly missing.
        if cnt > 0 and row[6]:
            # Sum for number of cases for the last 7 valid days.
            last_7_days_cases += int(row[6])
            cnt -= 1
        if cnt > 0:
            #Stops the loop from breaking if the sum has not completed but everything else has.
            continue

    deaths_recorded = False
    hospital_recorded = False
    skip_upto_incl = 0
    for row in covid_csv_data:
        if covid_csv_data.index(row) <= skip_upto_incl:
            #Skip this iteration
            continue

        if row[4] and not deaths_recorded:
            cumulative_deaths = int(row[4])
            deaths_recorded = True
        if row[5] and not hospital_recorded:
            current_hospital_cases = int(row[5])
            hospital_recorded = True

        if deaths_recorded and hospital_recorded:
            break #Data extracted

    return [last_7_days_cases, current_hospital_cases, cumulative_deaths]

def covid_API_hospital_cases_request(filters:list) -> Union[int, str]:
    """Carries out a COVID API data request for hospital cases and returns the result."""
    hospital_api = Cov19API(filters=filters, structure={"hospitalCases":"hospitalCases"}).get_json()

    for update in hospital_api["data"]:
        if update["hospitalCases"] is not None:
            hospital_cases = update["hospitalCases"]
            break
        logging.debug("API Data Missing: hospitalCases.")
    else: #No hospital stats available.
        hospital_cases = "N/A"
        logging.warning("Important data is missing from the API: Hospital cases.")

    return hospital_cases

def covid_API_request(location:str="Exeter",
                      location_type:str="ltla") -> dict:#
    """Carries out a COVID API data request and returns the result. Note that in this context,
updates are each a day's worth of COVID data, not an update defined by the user."""

    filters = [
        f"areaType={location_type}",
        f"areaName={location}"]
    if location_type == "nation":
        filters.pop(1)

    structure = {
        "date": "date",
        "cumDeaths28DaysByDeathDate": "cumDeaths28DaysByDeathDate",
        "newCasesByPublishDate": "newCasesByPublishDate"
    }
    if location_type != "nation":
        structure.pop("cumDeaths28DaysByDeathDate")

    api = Cov19API(
        filters=filters,
        structure=structure)

    updates = api.get_json() #Local variable

    most_recent_data = {}
    keys = list(structure.keys())

    exit_index = -1
    for update in updates["data"]:
        if all(update[key] is not None for key in keys):
            most_recent_data = update
            exit_index = updates["data"].index(update)
            break

    if most_recent_data == {}:
        logging.error("API Data Missing: ALL")
        return {} #No full set of data was obtained, so just exit here.

    ##Data: See structure
    most_recent_data["newCases7DaysByPublishDate"] = 0
    if len(updates["data"]) > exit_index + 7:
        #Add the new cases for the past week
        for item in updates["data"][exit_index : exit_index + 7]:
            if item["newCasesByPublishDate"] is not None:
                most_recent_data["newCases7DaysByPublishDate"] += item["newCasesByPublishDate"]
            else:
                logging.warning("API Data Missing: New weekly cases (for one of the days).")

    else:
        most_recent_data["newCases7DaysByPublishDate"] = "N/A"
        logging.error("API Data Missing: Cumulative infections from a week ago or older.")

    if location_type == "nation":
        most_recent_data["hospitalCases"] = covid_API_hospital_cases_request(filters)

    return most_recent_data

def schedule_covid_updates(update_name:str, update_interval:float) -> None:#
    """Base function for creating repetitive updates via add_update()."""
    try:
        update_interval = float(update_interval)
        cont = update_interval >= 0
    except ValueError:
        cont = False
    if cont:
        actions = [UpdateAction.REPETITIVE_REQUEST, UpdateAction.TIMED_REQUEST]
        add_update_with_checks(update_name, update_interval, "covid", actions)
    else:
        logging.error("[schedule_covid_updates] update_interval must be a float >= 0.")

def covid_update_request(local="Exeter", national="UK") -> None:
    """Uses covid_API_request to update the main webpage for scheduled updates."""
    global current_data

    local = covid_API_request(location=local, location_type="ltla")
    national = covid_API_request(location=national, location_type="nation")

    with open_utf8("data/config.json", "r") as file:
        json_file = json.load(file)

    json_file.update({
                    "location": "Exeter",
                    "nation_location": "UK",
                    "local_7day_infections": local["newCases7DaysByPublishDate"],
                    "national_7day_infections": national["newCases7DaysByPublishDate"],
                    "hospital_cases": national["hospitalCases"],
                    "deaths_total": national["cumDeaths28DaysByDeathDate"]})

    with open_utf8("data/config.json", "w") as file:
        json.dump(json_file, file, indent=4)

    current_data = json_file
