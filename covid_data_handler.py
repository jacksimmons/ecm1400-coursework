import csv
import json
import sched, time #Time scheduling modules
import logging
from uk_covid19 import Cov19API
import os

#0-9: NotSet, 10-19: Debug, 20-29: Info, 30-39: Warn, 40-49: Error, 50+: Critical
logging.basicConfig(level=logging.DEBUG, filename="data/covid_data_handler.log")
logging.debug("\n\n-----MODULE STARTUP-----")

s = sched.scheduler(time.time, time.sleep)
covid_scheduling_event = {}
current_API_call = {}

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

def covid_API_request(location="Exeter", location_type="ltla") -> dict:
    """Carries out a COVID API data request and returns the result."""
    loc_filters = [
        f"areaType={location_type}",
        f"areaName={location}"]
    structure = {
        "date": "date",
        "areaName": "areaName",
        "newCasesByPublishDate": "newCasesByPublishDate",
        "cumCasesByPublishDate": "cumCasesByPublishDate",
        "newDeaths28DaysByDeathDate": "newDeaths28DaysByDeathDate",
        "cumDeaths28DaysByDeathDate": "cumDeaths28DaysByDeathDate"
    }

    api = Cov19API(filters=loc_filters, structure=structure)
    updates = api.get_json()["data"]
    most_recent_data = {}
    missing_keys = list(structure.keys())
    for update in updates: #Iterate through every update until the most recent version of every stat has been obtained.
        if missing_keys != []: #Check that data is missing.
            for item in update:
                print(item)
                print(missing_keys)
                print(item in missing_keys)
                if update[item] is not None and item in missing_keys: #Use the most recent item for each stat which is not "None".
                    most_recent_data[item] = update[item]
                    missing_keys.remove(item)
                    if "date" in most_recent_data and update["date"] != most_recent_data["date"]:
                        logging.debug("API Data Missing (%s) has been replaced by data from %s. Original date: %s.",
                                        item,
                                        update["date"],
                                        most_recent_data["date"])
                elif item in missing_keys:
                    logging.debug("API Data Missing: %s.", item)
        else: #All data has been obtained; exit the loop.
            break

    print("UPDATES: \n" +str(updates))
    print("\n\n\n\n\nMOST RECENT: \n" +str(most_recent_data))

def schedule_covid_updates(update_interval:float, update_name:str):
    """Schedules COVID data updates at a regular interval, under an alias."""
    if covid_scheduling_event != {}:
        covid_scheduling_event["title"] = update_name
        covid_scheduling_event["event"] = s.enter(delay=update_interval,
                                                 priority=1,
                                                 action=covid_API_request)
        s.cancel()
    
covid_API_request()
#print(process_covid_csv_data(parse_csv_data(input("CSV FILENAME: "))))