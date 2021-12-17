from typing import Union

from core import get_data_from_file

from covid_data_handler import parse_csv_data
from covid_data_handler import process_covid_csv_data
from covid_data_handler import covid_API_request
from covid_data_handler import schedule_covid_updates

from covid_data_handler import covid_API_hospital_cases_request
from covid_data_handler import covid_update_request


def test_parse_csv_data(): #
    data = parse_csv_data('nation_2021-10-28.csv')
    assert len(data) == 639

def test_process_covid_csv_data(): #
    last7days_cases , current_hospital_cases , total_deaths = \
        process_covid_csv_data ( parse_csv_data (
            'nation_2021-10-28.csv' ) )
    assert last7days_cases == 240_299
    assert current_hospital_cases == 7_019
    assert total_deaths == 141_544

def test_covid_API_request(): #
    data = covid_API_request()
    assert isinstance(data, dict)
    print("COVID API data: " + str(data))

def test_schedule_covid_updates(): #
    #Normal
    schedule_covid_updates(update_interval=10, update_name="update test")
    #Boundary
    schedule_covid_updates(update_interval=0, update_name="update test 2")
    #Erroneous
    schedule_covid_updates(update_interval=-1, update_name=1)
    schedule_covid_updates(update_interval=1, update_name=1)
    schedule_covid_updates(update_interval="a", update_name="update test 3")
    schedule_covid_updates(update_interval=1, update_name="update test") # Duplicate name error

#test_parse_csv_data()
#test_process_covid_csv_data()
#test_covid_API_request()
#test_schedule_covid_updates()

#My Tests
def test_covid_API_hospital_cases_request():
    #Normal
    print("Location: UK")
    filters = [
        "areaType=nation"]
    cases = covid_API_hospital_cases_request(filters)
    assert isinstance(cases, Union[int, str])
    print(cases)

    #It seems the API has no data for Exeter's hospital cases
    print("Location: Exeter")
    filters = [
        "areaType=ltla",
        "areaName=Exeter"]
    cases = covid_API_hospital_cases_request(filters)
    assert isinstance(cases, Union[int, str])
    print(cases)

def test_covid_update_request():
    #Visual test - involves looking in config.json and at the website to confirm.
    update = {"title": "test",
         "interval": 0.0,
         "content":"Update covid, Repetitive, Interval (in seconds): 0.0",
         "repetitive": False}
    covid_update_request(update)
    print(get_data_from_file())
    #The data will be placed into config.json and onto the website

test_covid_API_hospital_cases_request()
test_covid_update_request()