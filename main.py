"""The main file of the project. Handles the scheduling loop and the Flask application."""

import json
import threading
import sched
import time

from flask import (
    Flask,
    render_template,
    request,
    redirect)

from covid_data_handler import (
    covid_update_request)
from covid_news_handling import (
    blacklist_article,
    update_news_request)
from core import (
    get_data_from_file,
    current_data,
    add_update_with_checks,
    remove_update,
    UpdateAction,
    open_utf8,
    logging_setup)

#Globals
name_error_counter = 0

###SCHEDULING
def do_updates() -> None:
    """Adds all of the updates in the global updates list to a scheduler, then runs that scheduler
    every time the scheduler'scheduler queue is empty. A never-ending procedure, so must be run in a
    separate thread to prevent the program from halting."""
    global current_data

    scheduler = sched.scheduler(time.time, time.sleep)
    current_data = get_data_from_file()

    while True:
        if not scheduler.queue: #If the scheduler queue is empty...
            if current_data["updates"] != []:
                for update in current_data["covid_updates"]:
                    scheduler.enter(update["interval"], 1, covid_update_request)
                    if not update["repetitive"]:
                        #If two identical updates exist, it doesn't matter which is removed.
                        remove_update(update["title"], "covid")
                scheduler.run()
                for update in current_data["news_updates"]:
                    scheduler.enter(update["interval"], 1, update_news_request)
                    if not update["repetitive"]:
                         #If two identical updates exist, it doesn't matter which is removed.
                        remove_update(update["title"], "news")
            else:
                time.sleep(1) #Prevent rapid continuous file reading and other expensive operations
                current_data = get_data_from_file()

###Startup
#Starts the infinite loop in a new thread
logging_setup()
update_runner = threading.Thread(None, do_updates)
update_runner.start()

###FLASK
app = Flask(__name__)
app.debug = True

@app.route("/")
def render_webpage():
    """Renders the root webpage."""
    global name_error_counter
    global current_data

    update_to_remove = request.args.get("update_item")
    article_to_remove = request.args.get("notif")

    if update_to_remove is not None:
        with open_utf8("data/config.json", "r") as file:
            json_file = json.load(file)
        covid_titles = [update["title"] for update in json_file["covid_updates"]]
        news_titles = [update["title"] for update in json_file["news_updates"]]
        if update_to_remove in covid_titles:
            remove_update(update_to_remove, "covid")
        if update_to_remove in news_titles:
            remove_update(update_to_remove, "news")
        return redirect(request.path)

    if article_to_remove is not None:
        blacklist_article(article_to_remove)
        return redirect(request.path)

    if name_error_counter >= 1:
        #Error has already been displayed and the webpage has been updated since, so remove error.
        current_data.pop("name_err")
        name_error_counter = 0

    if "name_err" in current_data:
        name_error_counter += 1

    current_data = get_data_from_file()
    return render_template(template_name_or_list="index.html", **current_data)

@app.route("/submit", methods=["POST"])
def submit_form():
    """Runs when the user clicks "Submit" on the website to add their update."""
    global name_error_counter

    if request.method == "POST":
        update_covid_data = request.form.get("covid-data")
        update_news_articles = request.form.get("news")
        name = request.form["two"]

        #If the update actually updates something...
        if not (update_covid_data is None and update_news_articles is None):
            names = [update["title"] for update in current_data["updates"]]
            if name not in names and name != "":
                #If the name is unique and valid...
                nice_interval = request.form["update"]
                #Convert "MM:SS" to seconds
                interval = float(nice_interval[:2]) * 60 + float(nice_interval[3:])
                repeat_update = request.form.get("repeat")

                content = []
                actions = []
                if repeat_update is not None:
                    content.append(UpdateAction.REPETITIVE_REQUEST)
                if update_covid_data is not None:
                    actions.append(UpdateAction.TIMED_REQUEST)
                    if repeat_update is not None:
                        #If repeat update is selected...
                        actions.append(UpdateAction.REPETITIVE_REQUEST)
                    add_update_with_checks(name, interval, "covid", actions)
                if update_news_articles is not None:
                    actions.append(UpdateAction.TIMED_REQUEST)
                    if repeat_update is not None:
                        #If repeat update is selected...
                        actions.append(UpdateAction.REPETITIVE_REQUEST)
                    add_update_with_checks(name, interval, "news", actions)
            else:
                current_data["name_err"] = "Name already taken."
                name_error_counter = 0

    return redirect("/")

###One-off events (don't occur when imported)
if __name__ == "__main__":
    app.run(use_reloader=False)
