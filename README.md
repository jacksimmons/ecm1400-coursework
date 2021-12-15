# Usage:
- Run "main.py" to start the application.
- Go to localhost:5000 or 127.0.0.1:5000 in your web browser.
- Now, use the available widgets to add and remove updates.
- You can customise the application settings in data/config.json.

- When you add an update which is both a COVID data and COVID news update, two separate updates are created (one covid_update and one news_update) with
- the same settings. When you remove one of them, the other is removed at the same time.
- Note that this behaviour persists even if you create the COVID data and COVID news updates separately, and even if they have different settings.
- This is intended behaviour as it allows the user to "link" a data and news update by one single name even if they have different intervals.

- You can add updates with an interval of at least 0 seconds.
- An interval of 0 seconds updates as frequently as possible.

# Glossary:
"cdata" refers to the module "covid_data_handler"
"cnews" refers to the module "covid_news_handling"

## Updates:
Updates are changes to the website's content, whether it be COVID statistics or News Articles.
Updates are all saved to data/config.json, and are loaded into memory at the start of the program and whenever an update is added or removed by the user.
Updates are timed and can be repeating.
News Updates and COVID statistics updates are stored under the aliases "news_updates" and "covid_updates" in data/config.json.
While a News Update and Covid Update (COVID statistics update) may share the same name, two of the same type of update cannot.

## Pylint Testing:
### Invalid Issues (marked by a - before them)
[C0103] current_data is not a constant.
[C0103] name_error_counter is not a constant.
[C0103] api_exhausted is not a constant.
[C0103] All of the function names are from the specification.

[W0611] The current_data import from core in covid_data_handler is flagged as unused because the module itself doesn't call
the only function that current_data is used in

### main
pylint main.py
************* Module main
-main.py:29:0: C0103: Constant name "name_error_counter" doesn't conform to UPPER_CASE naming style (invalid-name)
-main.py:36:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
main.py:36:4: W0603: Using the global statement (global-statement)
-main.py:72:4: C0103: Constant name "name_error_counter" doesn't conform to UPPER_CASE naming style (invalid-name)
main.py:72:4: W0603: Using the global statement (global-statement)
-main.py:73:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
main.py:73:4: W0603: Using the global statement (global-statement)
-main.py:107:4: C0103: Constant name "name_error_counter" doesn't conform to UPPER_CASE naming style (invalid-name)
main.py:107:4: W0603: Using the global statement (global-statement)

------------------------------------------------------------------
Your code has been rated at 8.98/10 (previous run: 8.98/10, +0.00)

### covid_data_handler
************* Module covid_data_handler
-covid_data_handler.py:67:20: C0103: Variable name "x" doesn't conform to snake_case naming style (invalid-name)
-covid_data_handler.py:87:0: C0103: Function name "covid_API_hospital_cases_request" doesn't conform to snake_case naming style (invalid-name)
-covid_data_handler.py:102:0: C0103: Function name "covid_API_request" doesn't conform to snake_case naming style (invalid-name)
-covid_data_handler.py:175:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
covid_data_handler.py:175:4: W0603: Using the global statement (global-statement)
-covid_data_handler.py:9:0: W0611: Unused current_data imported from core (unused-import)

------------------------------------------------------------------
Your code has been rated at 9.48/10 (previous run: 9.48/10, +0.00)

### covid_news_handler
************* Module covid_news_handling
-covid_news_handling.py:14:0: C0103: Constant name "api_exhausted" doesn't conform to UPPER_CASE naming style (invalid-name)
-covid_news_handling.py:18:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
covid_news_handling.py:18:4: W0603: Using the global statement (global-statement)
-covid_news_handling.py:33:0: C0103: Function name "news_API_request" doesn't conform to snake_case naming style (invalid-name)
-covid_news_handling.py:36:4: C0103: Constant name "api_exhausted" doesn't conform to UPPER_CASE naming style (invalid-name)
covid_news_handling.py:36:4: W0603: Using the global statement (global-statement)
-covid_news_handling.py:74:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
covid_news_handling.py:74:4: W0603: Using the global statement (global-statement)

------------------------------------------------------------------
Your code has been rated at 8.55/10 (previous run: 8.55/10, +0.00)

### core
************* Module core
-core.py:21:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
core.py:21:4: W0603: Using the global statement (global-statement)
-core.py:60:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
core.py:60:4: W0603: Using the global statement (global-statement)

------------------------------------------------------------------
Your code has been rated at 9.26/10 (previous run: 9.26/10, +0.00)

## Website Testing:
### Covid Updates
1-minute test succeeded.

## Referencing:
#https://stackoverflow.com/questions/24897644/is-there-a-way-to-change-pythons-open-default-text-encoding

        weekold_update = updates["data"][exit_index + 7]
        if weekold_update["cumCasesByPublishDate"] is not None: #Data was found from exactly a week ago: Best case scenario
            most_recent_data["newCases7DaysByPublishDate"] = most_recent_data["cumCasesByPublishDate"] - weekold_update["cumCasesByPublishDate"] #Cases in the last 7 days = Current cumulative cases - Current cumulative cases 7 days ago
        else:
            i = exit_index + 8
            logging.warning("API Data Missing: Cumulative infections one week ago. Replacing it with the next newest data.")
            while updates["data"][i]["cumCasesByPublishDate"] is None and i < len(updates["data"]):
                #Loop increments i until a data item is found, or 
                i += 1

            if i >= len(updates["data"]): #Then there were no older data items which matched. Worst case scenario: no data.
                most_recent_data["newCases7DaysByPublishDate"] = "N/A"
                logging.warning("API Data Missing: Replacement failed - no older replacement data.")
            else:
                most_recent_data["newCases7DaysByPublishDate"] = most_recent_data["cumCasesByPublishDate"] - updates["data"][i]["cumCasesByPublishDate"] #This will be >= the result if the data was present; it is an overestimate. Bad scenaerio.
                \.warning(
                
                
                
                
                API Data Found: {str(i - exit_index)} days early.") #How many days needed to be checked for replacement data to be found.


                def process_covid_csv_data(covid_csv_data:list) -> list[int]:#
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


    def add_update_check_name_valid(name:str, update_type:str) -> int:
    """Checks to see if the name provided is a duplicate name, or an empty string."""
    names = [update["title"] for update in current_data[f"{update_type}_updates"]]
    if name not in names and name != "":
        #If the name is unique and valid...
        nice_interval = request.form["update"]
        #Convert "MM:SS" to seconds
        interval = float(nice_interval[:2]) * 60 + float(nice_interval[3:])
        repeat_update = request.form.get("repeat")

        actions = []
        if repeat_update is not None:
            actions.append(UpdateAction.REPETITIVE_REQUEST)
        actions.append(UpdateAction.TIMED_REQUEST)
        add_update_with_checks(name, interval, update_type, actions)
    else:
        current_data["name_err"] = "Name already taken."
        name_error_counter = 0
    return name_error_counter