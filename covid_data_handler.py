from core \
    import UpdateAction, do_updates, add_update, remove_update

import csv
import sched, threading, time #Time scheduling modules
import logging
from uk_covid19 import Cov19API
from flask import Flask, render_template, request, redirect
from wtforms import StringField
import enum
#Everything in the below module is used by this file.
from covid_news_handling import *

###Logging
#0-9: NotSet, 10-19: Debug, 20-29: Info, 30-39: Warn, 40-49: Error, 50+: Critical
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG, filename="data/covid_data_handler.log")
logging.debug("\n\n-----MODULE STARTUP-----")

def parse_csv_data(csv_filename: str) -> list[str]:
    """Parses CSV file data into a list of lists (rows), each nested list representing a row in the file."""
    csv_data = []
    csv_current_row = []
    in_top_row = True
    with open(csv_filename, "r") as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            if in_top_row: ##Note: This is not good for general CSV files.
                # Skips the top row (column titles).
                in_top_row = False
                continue

            csv_current_row = [element for element in row]
            csv_data.append(csv_current_row)

        return csv_data

def process_covid_csv_data(covid_csv_data: list) -> list[int]:
    """Processes parsed COVID-19 CSV data and returns important statistics."""
    #areaCode,areaName,areaType,date,cumDailyNsoDeathsByDeathDate,hospitalCases,newCasesBySpecimenDate
    
    # NUMBER OF CASES IN THE LAST 7 DAYS
    last_7_days_cases = sum([(int(row[6]) if row[6] else 0) for row in covid_csv_data[:7]])
    # Above line sets a day's new cases to 0 if no data is provided.
    
    cnt = 7
    last_7_days_cases = 0
    data_extracted = False
    for row in covid_csv_data:
        if cnt > 0 and row[6]: ##Note: This won't give valid weekly readings if data is regularly missing.
            # Sum for number of cases for the last 7 valid days.
            last_7_days_cases += row[6]
            cnt -= 1
            
        if not(row[4] and row[5]): ##Note: de Morgan
            # If either are missing, continue.
            continue

        # Otherwise, extract data if this hasn't been done already.
        elif not data_extracted:
            # Need to use else if
            cumulative_deaths = row[4]
            current_hospital_cases = row[5]
            data_extracted = True

        if cnt > 0:
            # Stops the loop from breaking if the sum has not completed and the other data has been extracted.
            continue
        
        break # Exit the loop - data extracted and case sum complete.
    
    return [last_7_days_cases, current_hospital_cases, cumulative_deaths]

def covid_API_request(location:str="Exeter",
                      location_type:str="ltla",
                      days_recorded:int=14) -> dict:
    """Carries out a COVID API data request and returns the result."""
    date = get_date(offset=-14)

    #print(date)

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
                logging.warning("API Data Missing: New weekly cases (for one day). The resulting data will be inaccurate.")

    else:
        most_recent_data["newCases7DaysByPublishDate"] = "N/A"
        logging.error(f"API Data Missing: Cumulative infections from a week ago or older. Impossible to calculate newCases7DaysByPublishDate with the current method.")

    ##Extra Data: Hospital Cases
    if location_type == "nation":
        hospital_api = Cov19API(filters=filters, structure={"hospitalCases": "hospitalCases"}).get_json()

        for update in hospital_api["data"]:
            if update["hospitalCases"] is not None:
                most_recent_data["hospitalCases"] = update["hospitalCases"]
                break
            else:
                logging.debug("API Data Missing: hospitalCases.")
                continue
        else:
            if "hospitalCases" not in most_recent_data:
                most_recent_data["hospitalCases"] = "N/A"
                logging.warning("Important data is missing from the API: Any data on the number of hospital cases.")

    return most_recent_data

def covid_update_request(local="Exeter", national="UK") -> None:
    """Uses covid_API_request to update the main webpage for scheduled updates."""
    local = covid_API_request(location=local, location_type="ltla", days_recorded=14)
    national = covid_API_request(location=national, location_type="nation", days_recorded=14)

    current_data.update({
                    "location": "Exeter",
                    "nation_location": "UK",
                    "local_7day_infections": local["newCases7DaysByPublishDate"],
                    "national_7day_infections": national["newCases7DaysByPublishDate"],
                    "hospital_cases": national["hospitalCases"],
                    "deaths_total": national["cumDeaths28DaysByDeathDate"]})

def schedule_covid_updates(update_name:str, update_interval:int) -> None:
    """Base function for creating repetitive updates via core.add_update()."""
    #Adds an update with three features: it is a covid update, repeating, and timed (an update must be timed).
    covid_update_request()
    add_update(update_name, update_interval, [UpdateAction.COVID_UPDATE_REQUEST, UpdateAction.REPETITIVE_REQUEST, UpdateAction.TIMED_REQUEST])