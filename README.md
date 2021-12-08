#Glossary:#
"cdata" refers to the module "covid_data_handler"
"cnews" refers to the module "covid_news_handling"

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
                logging.warning(f"API Data Found: {str(i - exit_index)} days early.") #How many days needed to be checked for replacement data to be found.