import csv
import json
import sched, threading, time, datetime #Time scheduling modules
import logging
from uk_covid19 import Cov19API
from flask import Flask, render_template, request, redirect
from wtforms import StringField
import enum

class UpdateAction(enum.Enum):
    COVID_UPDATE_REQUEST    = 0
    NEWS_UPDATE_REQUEST     = 1
    REPETITIVE_REQUEST      = 2
    TIMED_REQUEST           = 3

updates = []
covid_scheduling_event = {}
current_data = {"updates": updates}
name_error_counter = 0

#0-9: NotSet, 10-19: Debug, 20-29: Info, 30-39: Warn, 40-49: Error, 50+: Critical
logging.basicConfig(level=logging.DEBUG, filename="data/covid_data_handler.log")
logging.debug("\n\n-----MODULE STARTUP-----")

###Other functions
def get_date(offset:int=0) -> str:
    """Returns the date + the offset in YYYY-MM-DD format."""
    date = datetime.datetime.today() + datetime.timedelta(days=offset)
    return date.strftime("%Y-%m-%d")

def do_updates() -> None:
    """Adds all of the updates in the global updates list to a scheduler, then runs that scheduler
    every time the scheduler's queue is empty. A never-ending procedure, so must be run in a separate
    thread to prevent the program from halting."""
    s = sched.scheduler(time.time, time.sleep)
    while True:
        if s.queue == []: #If the queue is empty, repopulate the queue.
            for update in updates:
                #print(update["name"])
                for call in update["calls"]:
                    s.enter(update["interval"], 1, call)
                if not update["repetitive"]:
                    updates.remove(update) #If two identical updates exist, it doesn't matter which is removed.
            s.run()

def add_update(name:str, nice_interval:str, actions:list) -> None:
    """Reformats and adds an update to the global updates list.
    nice_interval: An interval formatted as a MM:SS string."""
    content = ""
    calls = []
    repetitive = False
    interval = float(nice_interval[:2]) * 60 + float(nice_interval[3:]) #Convert "MM:SS" to seconds
    for action in actions: #Convert enum values to corresponding readable string values
        if action == UpdateAction.COVID_UPDATE_REQUEST:
            if content != "":
                content += ", "
            content += "Update Covid Data"
            calls.append(covid_update_request)
        elif action == UpdateAction.NEWS_UPDATE_REQUEST:
            if content != "":
                content += ", "
            content += "Update News Articles"
        elif action == UpdateAction.REPETITIVE_REQUEST: #Sets the request to be repetitive
            if content != "":
                content += ", "
            content += "Repeating"
            repetitive = True
        elif action == UpdateAction.TIMED_REQUEST: #Sets the request to be timed. All requests are timed requests
            if content != "":
                content += ", "
            content += f"Interval [MM:SS]: {nice_interval}"

    update = {"title":name, "interval": interval, "content":content, "calls":calls, "repetitive":repetitive}
    updates.append(update)
    #No need to refresh current_data["updates"] as updates is mutable.

def remove_update(name:str) -> None:
    """Removes an update by name."""
    for update in updates:
        if update["title"] == name:
            updates.remove(update)
            break

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
        "cumCasesByPublishDate": "cumCasesByPublishDate",
        "cumDeaths28DaysByDeathDate": "cumDeaths28DaysByDeathDate"
    }
    if location_type == "nation":
        structure.pop("cumDeaths28DaysByDeathDate")

    api = Cov19API(
        filters=filters,
        structure=structure)

    updates = api.get_json()

    most_recent_data = {}
    missing_keys = list(structure.keys())

    cumCasesAvailable = True
    for missing_key in missing_keys: #Check there are non-None entries for each data item so that the program doesn't iterate through the entire API data dictionary expensively.
        if not all(update[missing_key] is not None for update in updates["data"]): #If there is a key for which there is no non-None value in the API data
            most_recent_data[missing_key] = "N/A"
            missing_keys.remove(missing_key)
            if missing_key == "cumCasesByPublishDate":
                cumCasesAvailable = False #Means the while cumCasesAvailable loop never enters; it is not possible to calculate the new cases in the past week without cumulative cases.

    for update in updates["data"]: #Iterate through every update until the most recent version of every stat has been obtained.
        if missing_keys != []: #Check that data is missing.
            #print("Missing Keys: " + str(missing_keys))
            #print("Update: " + str(update))

            for item in update:
                #print("Item: " + item)
                if update[item] is not None and item in missing_keys: #Use the most recent item for each stat which is not "None".
                    most_recent_data[item] = update[item]
                    #print(most_recent_data)
                    missing_keys.remove(item)
                    if "date" in most_recent_data and update["date"] != most_recent_data["date"]:
                        logging.debug("API Data Missing (%s) has been replaced by data from %s. Original date: %s.",
                                        item,
                                        update["date"],
                                        most_recent_data["date"])
                elif item in missing_keys:
                    logging.debug("API Data Missing: %s.", item)
            continue #Don't want to exit the loop yet.

        cnt = 0
        while cumCasesAvailable: #Last thing to do is to subtract the cumCasesByPublishDate of the date 7 days ago from the current cumCasesByPublishDate.
            #If that fails, we resort to the closest date after 7 days ago. (Iterate over every day until valid data has been found)
            #print(cnt)
            try:
                cumCases7PlusCntDaysAgo = updates["data"][updates["data"].index(update) + 7 + cnt]["cumCasesByPublishDate"]
                if cumCases7PlusCntDaysAgo is not None:
                    most_recent_data["newCases7DaysByPublishDate"] = most_recent_data["cumCasesByPublishDate"] - cumCases7PlusCntDaysAgo
                    break
                else:
                    cnt += 1
            except IndexError: #The API should always have data from 7 days ago or older, so this is an extreme catch.
                #Impossible to calculate; every cumCasesByPublishDate data item with age >= 7 days is NoneType.
                logging.warning("Important data is missing from the API: Cumulative cases from 7 days and older. This makes it impossible to truthfully calculate the new cases over the past week.")
                most_recent_data["newCases7DaysByPublishDate"] = "N/A"
                break
        else:
            if not cumCasesAvailable: #elif not supported by while. This statement is to ensure that only cumCasesAvailable being False before the loop began can cause this code to be executed.
                most_recent_data["newCases7DaysByPublishDate"] = "N/A"
        break #No need to stay in the loop.

    if location_type == "ltla":
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

    #print("\nMOST RECENT: \n" +str(most_recent_data))
    return most_recent_data

def covid_update_request() -> None:
    """Uses covid_API_request to update the main webpage for scheduled updates."""
    #print("---Update req---")
    #print("LOCAL")
    print("Update")
    local = covid_API_request(location="Exeter", location_type="ltla", days_recorded=14)
    #print("NATIONAL")
    national = covid_API_request(location="UK", location_type="nation", days_recorded=14)

    global current_data
    current_data.update({
                    "location": "Exeter",
                    "nation_location": "UK",
                    "local_7day_infections": local["newCases7DaysByPublishDate"],
                    "national_7day_infections": national["newCases7DaysByPublishDate"],
                    "hospital_cases": local["hospitalCases"],
                    "deaths_total": local["cumDeaths28DaysByDeathDate"]})
    
#print(process_covid_csv_data(parse_csv_data(input("CSV FILENAME: "))))

###FLASK
def create_app():
    """Creates and returns the Flask application."""
    app = Flask(__name__)
    app.debug = True
    return app
app = create_app()

@app.route("/")
def render_webpage():
    """Renders the root webpage."""
    global name_error_counter
    item_to_remove = request.args.get("update_item")
    if item_to_remove is not None:
        remove_update(item_to_remove)
    if name_error_counter >= 1:
        current_data.pop("name_err")#Error has already been displayed and the webpage has been updated since, so remove error.
        name_error_counter = 0
    if "name_err" in current_data:
        name_error_counter += 1
    return render_template(template_name_or_list="index.html", **current_data)

@app.route("/submit", methods=["POST"])
def submit_form():
    print(request.method)
    if request.method == "POST":
        update_covid_data = request.form.get("covid-data")
        update_news_articles = request.form.get("news")
        name = request.form["two"]

        if not (update_covid_data is None and update_news_articles is None): #If the update actually updates something
            if name not in (update["title"] for update in updates): #If the name provided is unique
                duration = request.form["update"]
                repeat_update = request.form.get("repeat")

                print(repeat_update) #None is standard for unchecked checkbox.
                print(update_covid_data)
                print(update_news_articles)

                content = []
                if update_covid_data is not None:
                    content.append(UpdateAction.COVID_UPDATE_REQUEST)
                if update_news_articles is not None:
                    content.append(UpdateAction.NEWS_UPDATE_REQUEST)
                if repeat_update is not None:
                    content.append(UpdateAction.REPETITIVE_REQUEST)
                content.append(UpdateAction.TIMED_REQUEST)

                add_update(name, duration, content) #also needs news update compatibility
            else:
                current_data["name_err"] = "Name already taken."
                name_error_counter = 0

    return redirect("/")

###Startup commands and global variable creation
add_update("Bruh", "00:03", [UpdateAction.COVID_UPDATE_REQUEST])
update_runner = threading.Thread(None, do_updates) #Runs an infinite loop of executing updates asynchronously so the rest of the program runs in parallel.
update_runner.start()
###End of Startup

###Finalisation
if __name__ == "__main__":
    app.run()