import base64
import math
import os
import random
import time
from functools import wraps

import requests
from flask import abort, Flask, render_template, request, session
from redis import StrictRedis
from simpleflake import simpleflake
from werkzeug.exceptions import TooManyRequests

CHIKKA_API_URL = "https://post.chikka.com/smsapi/request"

SHORTCODE = os.environ["CHIKKA_SHORTCODE"]
CLIENT_ID = os.environ["CHIKKA_CLIENT_ID"]
SECRET_KEY = os.environ["CHIKKA_SECRET_KEY"]

app = Flask(__name__)
app.config.update(SECRET_KEY=os.environ["SECRET_KEY"])
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


def gen_csrf_token():
    return base64.b64encode(os.urandom(32))


def rate_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        last_req_key = "last_req:" + request.headers.get(
            'X-Forwarded-For', request.remote_addr)
        last_req = db.get(last_req_key)
        now = int(time.time())
        if request.method == "POST":
            if last_req:
                limit_end = int(last_req) + 30 * 60
                remaining = limit_end - now
                if remaining > 0:
                    raise TooManyRequests("Try again in {} minutes.".format(
                        int(math.ceil(remaining / 60.))
                    ))
            try:
                resp = f(*args, **kwargs)
            except Exception:
                raise
            else:
                db.set(last_req_key, now)
                return resp
        else:
            return f(*args, **kwargs)
    return decorated


@app.route("/", methods=["GET", "POST"])
@rate_limit
def index():
    context = {}
    if request.method == "GET":
        if "csrf_token" not in session:
            session["csrf_token"] = gen_csrf_token()
        context.update(csrf_token=session["csrf_token"])
    elif request.method == "POST":
        csrf_token = session.get("csrf_token")
        if not csrf_token:
            abort(401)
        if request.form["csrf_token"] != csrf_token:
            abort(401)
        names = request.form.getlist("name")
        numbers = request.form.getlist("number")
        members = zip(names, numbers)
        if not members:
            abort(400)
        theme = request.form.get("theme", "").strip()
        # Record theme for stats purposes
        db.sadd("themes", theme)
        random.shuffle(members)
        for i, [name, number] in enumerate(members):
            assigned_name, _ = members[(i + 1) % len(members)]
            message = "Hi, {}. You drew {} for our Monito-monita! ".format(
                name, assigned_name)
            if theme:
                message += "Our theme is \"{}\". ".format(theme)
            send_sms(number, message)
        context.update(has_drawn=True, members=members)
        session.clear()
    else:
        abort(405)
    return render_template("index.html", **context)


@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(429)
def error(error):
    return render_template("error.html", error=error)


if __name__ == "__main__":
    app.run(debug=True)

