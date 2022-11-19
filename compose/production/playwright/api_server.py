from flask import Flask
from flask import request
from playwright.sync_api import sync_playwright

app = Flask(__name__)
pw = sync_playwright().start()
chrome = pw.chromium.launch(headless=True)


# create a view that take POST request contain url param, and return the html
@app.route("/scrape", methods=["POST"])
def scrape():
    url = request.get_json().get("url")
    page = chrome.new_page()
    page.goto(url)
    html = page.content()
    page.close()
    return html


@app.route("/", methods=["GET"])
def index():
    return "Hello World"


if __name__ == "__main__":
    app.run(threaded=False, host="0.0.0.0", port=5000)
