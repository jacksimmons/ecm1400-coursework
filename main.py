"""The main file of the project. Handles the scheduling loop and the Flask application."""

import json
import threading
import sched
import time

from typing import Callable

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
    logging_setup,
    updates_scheduled)

#Globals
update_name_taken_error = False

###SCHEDULING
def launch_scheduler_thread(scheduler:sched.scheduler, update:dict, action:Callable, priority:int):
    """A procedure which starts a new thread with a single scheduled event in it."""

    def start_scheduler(scheduler:sched.scheduler, update:dict, action:Callable, priority:int):
        """Starts the scheduler. Required as the Thread needs to call something."""
        scheduler.enter(update["interval"], priority, action, (update))
        scheduler.run()

    threading.Thread(None, start_scheduler(scheduler, update["title"], update["interval"], action))

def do_updates() -> None:
    """Adds all of the updates in the global updates list to a scheduler, then runs that scheduler
    every time the scheduler'scheduler queue is empty. A never-ending procedure, so must be run in
    a separate thread to prevent the program from halting."""
    global current_data
    current_data = get_data_from_file()

    scheduler = sched.scheduler(time.time, time.sleep)

    while True:
        if current_data["updates"] != []:
            for update in current_data["covid_updates"]:
                if update not in updates_scheduled:
                    if not update["repetitive"]:
                        #If two identical updates exist, it doesn't matter which is removed.
                        remove_update(update["title"], "covid")
                        #This is passed to covid_data_request.
                        update["title"] = "Non-Repetitive"
                    launch_scheduler_thread(scheduler, update, covid_data_request, 1)
                    updates_scheduled.append(update)
            for update in current_data["news_updates"]:
                if update not in updates_scheduled:
                    if not update["repetitive"]:
                        #If two identical updates exist, it doesn't matter which is removed.
                        remove_update(update["title"], "news")
                        #This is passed to update_news_request.
                        update["title"] = "Non-Repetitive"
                    launch_scheduler_thread(scheduler, update, update_news_request, 1)
                    updates_scheduled.append(update)
            scheduler.run()

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
    global update_name_taken_error
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
        for article in current_data["news_articles"]:
            if article["title"] == article_to_remove:
                #Blacklist the first URL to match the title provided.
                blacklist_article(article)
                return redirect(request.path)

    if update_name_taken_error:
        #Make the error disappear upon next "submit".
        update_name_taken_error = False
    else:
        with open_utf8("data/config.json", "r") as file:
            data = json.load(file)
        data["name_err"] = "" #Remove the name error
        with open_utf8("data/config.json", "w") as file:
            json.dump(data, file, indent=4)

    current_data = get_data_from_file()

    return render_template(template_name_or_list="index.html", **current_data)

@app.route("/submit", methods=["POST"])
def submit_form():
    """Runs when the user clicks "Submit" on the website to add their update."""
    global update_name_taken_error

    if request.method == "POST":
        update_covid_data = request.form.get("covid-data")
        update_news_articles = request.form.get("news")
        name = request.form["two"]

        nice_interval = request.form["update"]
        #Convert "MM:SS" to seconds
        interval = float(nice_interval[:2]) * 60 + float(nice_interval[3:])
        repeat_update = request.form.get("repeat")

        actions = []
        if repeat_update is not None:
            actions.append(UpdateAction.REPETITIVE_REQUEST)
        actions.append(UpdateAction.TIMED_REQUEST)

        #If the update actually updates something...
        if update_covid_data is not None:
            update_name_taken_error = add_update_with_checks(name, interval, "covid", actions)
        if update_news_articles is not None:
            if not update_name_taken_error: #If no covid update error already (error is shared)
                update_name_taken_error = add_update_with_checks(name, interval, "news", actions)

    return redirect("/")

if __name__ == "__main__":
    app.run(use_reloader=False)
