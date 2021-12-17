"""The main file of the project. Handles the scheduling loop and the Flask application."""

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
    write_data_to_file,
    current_data,
    add_update_with_checks,
    remove_update,
    UpdateAction)

#Globals
update_name_taken_error = False

###SCHEDULING
def do_updates() -> None:
    """Uses multithreading to start multiple scheduling events (the updates) at once."""
    def schedule_update(interval:float, action:Callable, update:dict, priority:int=1) -> None:
        """Uses sched to schedule an update."""
        scheduler = sched.scheduler(time.time, time.sleep)
        while update in current_data["updates_scheduled"] and update["repetitive"]:
            if not scheduler.queue: # == []
                scheduler.enter(interval,
                        priority,
                        action,
                        kwargs={"update": update})
            scheduler.run()

        if not update["repetitive"]:
            #Execute once instead
            scheduler.enter(interval,
                        priority,
                        action,
                        kwargs={"update": update})
            scheduler.run()

        if not update["repetitive"]:
            #The update is not repetitive so remove it.
            remove_update(update["title"], "covid")

    current_data["updates_scheduled"] = []
    current_data["covid_updates_scheduled"] = []
    current_data["news_updates_scheduled"] = []
    write_data_to_file(current_data)

    startup = False

    while True:
        if len(current_data["updates"]) > len(current_data["updates_scheduled"]) or startup:
            #Update whenever there are updates waiting for scheduling.
            startup = False
            for update in current_data["covid_updates"]:
                if update not in current_data["covid_updates_scheduled"]:
                    #Only schedule the covid updates which need scheduling.

                    current_data["covid_updates_scheduled"].append(update)
                    current_data["updates_scheduled"].append(update)
                    write_data_to_file(current_data)
                    update_thread = threading.Thread(None,
                                                        schedule_update,
                                                        args = (
                                                        update["interval"],
                                                        covid_update_request,
                                                        update,
                                                        1),
                                                        name=update["title"])
                    update_thread.start()

            for update in current_data["news_updates"]:
                if update not in current_data["news_updates_scheduled"]:
                    #Only schedule the news updates which need scheduling.

                    current_data["news_updates_scheduled"].append(update)
                    current_data["updates_scheduled"].append(update)
                    write_data_to_file(current_data)
                    update_thread = threading.Thread(None,
                                                        schedule_update,
                                                        args = (
                                                        update["interval"],
                                                        update_news_request,
                                                        update,
                                                        1),
                                                        name=update["title"])
                    update_thread.start()

###Startup
#Starts the infinite loop in a new thread
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

    #If user chose to remove an update
    if update_to_remove is not None:
        json_file = get_data_from_file()
        covid_titles = [update["title"] for update in json_file["covid_updates"]]
        news_titles = [update["title"] for update in json_file["news_updates"]]
        if update_to_remove in covid_titles:
            remove_update(update_to_remove, "covid")
        if update_to_remove in news_titles:
            remove_update(update_to_remove, "news")
        return redirect(request.path)

    #If user chose to remove an article
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
        data = get_data_from_file()
        data["name_err"] = "" #Remove the name error
        write_data_to_file(data)

    current_data = get_data_from_file()
    return render_template(template_name_or_list="index.html", **current_data)

@app.route("/submit", methods=["POST"])
def submit_form():
    """Runs when the user clicks "Submit" on the website to add their update."""
    #NOTE: an added update will not be scheduled until all other updates have finished.
    #(See Usage:4 in README.md)
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
