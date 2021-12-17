# Github:
https://github.com/piklman/covid-dash

# Usage:
- Python version: 3.10 (64-bit)
- Run "main.py" to start the application. (F5 or Ctrl+F5)
- Go to localhost:5000 or 127.0.0.1:5000 in your web browser.
- Now, use the available widgets to add and remove updates.
- Adding an update without any of the 3 checkboxes ticked, or just repeating ticked will not give an error but also won't do anything.
- You can customise the application settings in data/config.json (config.json).

- When you add an update which is both a COVID data and COVID news update, two separate updates are created (one covid_update and one news_update) with
the same settings. When you remove one of them, the other is removed at the same time.
- Note that this behaviour persists even if you create the COVID data and COVID news updates separately, and even if they have different settings.
- This allows the user to "link" a data and news update by one single name even if they have different intervals or if one is repeating and the other isn't.

- You can add updates with an interval of at least 0 seconds.
- An interval of 0 seconds updates as frequently as possible, but this will likely be only once every second or two.

- When you remove an article, it will not return unless you remove it from "blacklisted_articles" from config.json.
- When you remove an update, it will complete its next scheduled update and not update again.

- If you want to reset all of your updates, articles and other settings, copy and paste the contents of config_empty.json into config.json.

- To access the log, go to "data/log.log" (log.log).

- You can change config.json manually if the program is not running (for editing updates, etc.).
- Changing it while it is running is possible but may cause issues.
- Updates will continue to work after restarting the program.

- See Assumptions and design choices for more information.

# config.json settings:
- csv_skip_first_entry - Whether or not the first entry in the CSV file is to be skipped (it needs to be skipped in nation_2021-10-28.csv as it contains incomplete data, but if you are are using the CSV procedures for other data, turning this to false may be useful.

- log_level - sets the logging level to that value.
 CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10
NOTSET = 0

# Assumptions and design choices:
- Updates take a couple of seconds to process, so a 5 second COVID data update may take 7 seconds and a 10 second one may take 12 seconds.
- This means an update with interval x will have a frequency less than twice that of an update with an interval of 2x.

- In my program, I assumed that {{hospital_cases}} from the template meant "National Hospital Cases", and that {{deaths_total}} meant "National Total Deaths".
- As a result, these data are excluded from covid_API_request whenever a location_type other than "nation" is chosen.

- On the website, I added a label for "National Hospital Cases" [{{hospital_cases}}] and "National Total Deaths" [{{deaths_total}}] as they had no labels.
- I added an error label below the Update Label to show the user when and why an error has occurred.

- For covid update requests, to obtain the weekly cases data, I added the cases for the previous 6 days before the most recent day with cases data.
- For any missing cases data in those 6 days, nothing is added and this is shown in the log. This method should produce very accurate data unless the covid API has data present for one day and not for days before it, which is extremely unlikely.

- For the data in covid updates, for the local data and the national data separately, the data is based on the most recent day (and the 6 days before it for 7 day local cumulative cases) for which all of the data is available. As a result, if the data provided is incomplete, this may lead to inconsistent output.

- Due to the large loading times for updates, blacklisting articles or removing updates may clash in file access with an existing update when the update's interval is up.
- As a result, the shorter the interval, the more likely collisions are to occur.
- Operations still occur in collisions as one of the two waits, however some "progress" on current_data may be lost. (So your blacklist of an article, for example, will need to be done again.)

# Updates:
Updates are changes to the website's content, whether it be COVID statistics or News Articles.
Updates are all saved to data/config.json, and are loaded into memory at the start of the program and whenever an update is added or removed by the user.
Updates are timed and can be repeating.
News Updates and COVID statistics updates are stored under the aliases "news_updates" and "covid_updates" in data/config.json.
While a News Update and Covid Update (COVID statistics update) may share the same name, two of the same type of update cannot.

# Pylint Testing:
## Invalid Issues (marked by a - before them)
[C0103] current_data is not a constant.
[C0103] name_error_counter is not a constant.
[C0103] api_exhausted is not a constant.
[C0103] update_name_taken_error is not a constant.
[C0103] adding_update is not a constant.
[C0103] All of the function names are from the specification.

[W0611] The current_data import from core in covid_data_handler is flagged as unused because the module itself doesn't call
the only function that current_data is used in

## main
************* Module main
-main.py:29:0: C0103: Constant name "update_name_taken_error" doesn't conform to UPPER_CASE naming style (invalid-name)
-main.py:114:4: C0103: Constant name "update_name_taken_error" doesn't conform to UPPER_CASE naming style (invalid-name)
main.py:114:4: W0603: Using the global statement (global-statement)
-main.py:115:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
main.py:115:4: W0603: Using the global statement (global-statement)
-main.py:155:4: C0103: Constant name "update_name_taken_error" doesn't conform to UPPER_CASE naming style (invalid-name)
main.py:155:4: W0603: Using the global statement (global-statement)

------------------------------------------------------------------
Your code has been rated at 9.26/10 (previous run: 9.05/10, +0.20)

## covid_data_handler
************* Module covid_data_handler
-covid_data_handler.py:92:0: C0103: Function name "covid_API_hospital_cases_request" doesn't conform to snake_case naming style (invalid-name)
-covid_data_handler.py:107:0: C0103: Function name "covid_API_request" doesn't conform to snake_case naming style (invalid-name)
-covid_data_handler.py:180:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
covid_data_handler.py:180:4: W0603: Using the global statement (global-statement)
-covid_data_handler.py:7:0: W0611: Unused current_data imported from core (unused-import)

------------------------------------------------------------------
Your code has been rated at 9.57/10 (previous run: 9.48/10, +0.09)

************* Module covid_news_handling
-covid_news_handling.py:14:0: C0103: Constant name "api_exhausted" doesn't conform to UPPER_CASE naming style (invalid-name)
-covid_news_handling.py:18:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
covid_news_handling.py:18:4: W0603: Using the global statement (global-statement)
-covid_news_handling.py:29:0: C0103: Function name "news_API_request" doesn't conform to snake_case naming style (invalid-name)
-covid_news_handling.py:32:4: C0103: Constant name "api_exhausted" doesn't conform to UPPER_CASE naming style (invalid-name)
covid_news_handling.py:32:4: W0603: Using the global statement (global-statement)
-covid_news_handling.py:70:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
covid_news_handling.py:70:4: W0603: Using the global statement (global-statement)

------------------------------------------------------------------
Your code has been rated at 8.40/10 (previous run: 8.00/10, +0.40)

## core
************* Module core
-core.py:16:0: C0103: Constant name "adding_update" doesn't conform to UPPER_CASE naming style (invalid-name)
-core.py:59:4: C0103: Constant name "adding_update" doesn't conform to UPPER_CASE naming style (invalid-name)
core.py:59:4: W0603: Using the global statement (global-statement)
-core.py:60:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
core.py:60:4: W0603: Using the global statement (global-statement)
-core.py:87:4: C0103: Constant name "adding_update" doesn't conform to UPPER_CASE naming style (invalid-name)
core.py:87:4: W0603: Using the global statement (global-statement)
-core.py:114:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
core.py:114:4: W0603: Using the global statement (global-statement)
-core.py:150:4: C0103: Constant name "current_data" doesn't conform to UPPER_CASE naming style (invalid-name)
core.py:150:4: W0603: Using the global statement (global-statement)

------------------------------------------------------------------
Your code has been rated at 8.90/10 (previous run: 8.81/10, +0.09)

# pytest:
platform win32 -- Python 3.10.0, pytest-6.2.5, py-1.11.0, pluggy-1.0.0
rootdir: Programming Coursework
collected 16 items

test_core.py ......                                                                                              [ 37%]
test_covid_data_handler.py ......                                                                                [ 75%]
test_news_data_handling.py ....                                                                                  [100%]

================================================= 16 passed in 4.49s ==================================================

# Website Testing:
Covid, Non-Repeating - Success
Covid, Repeating - Success
News, Non-Repeating - Success
News, Repeating - Success
Covid and News, Non-Repeating - Success
Covid and News, Repeating - Success

Covid, Repeating after restarting the program - Success
Two updates in parallel - Success

## Referencing:
https://stackoverflow.com/questions/24897644/is-there-a-way-to-change-pythons-open-default-text-encoding
https://stackoverflow.com/questions/2507808/how-to-check-whether-a-file-is-empty-or-not