from flask import Flask, render_template
import covid_data_handler as c_data
import covid_news_handling as c_news
import os
print(os.getcwd())

def create_app():
    # Create and return Flask application
    app = Flask(__name__)
    return app

app = create_app()

@app.route("/")
def func():
    
    return render_template('index.html', )

if __name__ == "__main__":
    app.run()