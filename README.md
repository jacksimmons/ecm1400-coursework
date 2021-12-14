#Glossary:#
"cdata" refers to the module "covid_data_handler"
"cnews" refers to the module "covid_news_handling"

##Updates:##
Updates are changes to the website's content, whether it be COVID statistics or News Articles.
Updates are all saved to data/config.json, and are loaded into memory at the start of the program and whenever an update is added or removed by the user.
Updates are timed and can be repeating.
News Updates and COVID statistics updates are stored under the aliases "news_updates" and "covid_updates" in data/config.json.
While a News Update and Covid Update (COVID statistics update) may share the same name, two of the same type of update cannot.

##Pylint Testing:##
#Invalid Issues (marked by a - before them)
[C0103] current_data is not a constant.
[C0103] name_error_counter is not a constant.
[C0103] api_exhausted is not a constant.
[C0103] All of the function names are from the specification.

[W0611] The current_data import from core in covid_data_handler is flagged as unused because the module itself doesn't call
the only function that current_data is used in

#main
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

#covid_data_handler
************* Module covid_data_handler
-covid_data_handler.py:67:0: C0103: Function name "covid_API_hospital_cases_request" doesn't conform to snake_case naming style (invalid-name)
-covid_data_handler.py:83:0: C0103: Function name "covid_API_request" doesn't conform to snake_case naming style (invalid-name)
-covid_data_handler.py:156:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
covid_data_handler.py:156:4: W0603: Using the global statement (global-statement)
-covid_data_handler.py:9:0: W0611: Unused current_data imported from core (unused-import)

------------------------------------------------------------------
Your code has been rated at 9.52/10 (previous run: 9.52/10, +0.00)

#covid_news_handler
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

#core
************* Module core
-core.py:21:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
core.py:21:4: W0603: Using the global statement (global-statement)
-core.py:60:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
core.py:60:4: W0603: Using the global statement (global-statement)

------------------------------------------------------------------
Your code has been rated at 9.25/10 (previous run: 9.25/10, +0.00)


##Referencing:##
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