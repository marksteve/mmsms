import os
import random

import requests
from flask import Flask, render_template, request
from redis import StrictRedis
from simpleflake import simpleflake

CHIKKA_API_URL = "https://post.chikka.com/smsapi/request"

SHORTCODE = os.environ["CHIKKA_SHORTCODE"]
CLIENT_ID = os.environ["CHIKKA_CLIENT_ID"]
SECRET_KEY = os.environ["CHIKKA_SECRET_KEY"]

app = Flask(__name__)
db = StrictRedis(host=os.environ.get("REDIS_HOST", "localhost"))


def send_sms(mobile_number, message):
  requests.post(
    CHIKKA_API_URL,
    data=dict(
      message_type="SEND",
      mobile_number=mobile_number,
      shortcode=SHORTCODE,
      message_id=str(simpleflake()),
      message=message,
      client_id=CLIENT_ID,
      secret_key=SECRET_KEY,
    )
  )


@app.route("/", methods=["GET", "POST"])
def index():
    context = {}
    if request.method == "POST":
        names = request.form.getlist("name")
        numbers = request.form.getlist("number")
        theme = request.form.get("theme", "").strip()
        db.sadd("themes", theme)  # For stats purposes :)
        members = zip(names, numbers)
        random.shuffle(members)
        for i, [name, number] in enumerate(members):
            assigned_name, _ = members[(i + 1) % len(members)]
            message = "Hi, {}. You drew {} for our Monito-monita! ".format(
                name, assigned_name)
            if theme:
                message += "Our theme is \"{}\". ".format(theme)
            send_sms(number, message)
        context.update(has_drawn=True)
    return render_template("index.html", **context)


if __name__ == "__main__":
    app.run(debug=True)
