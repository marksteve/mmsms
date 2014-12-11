import random

import redis
import tortilla
from flask import Flask, render_template, request
from simpleflake import simpleflake

SHORTCODE = "21581734"


app = Flask(__name__)
app.config.from_pyfile('config.py')
db = redis.StrictRedis(host="redis")
chikka = tortilla.wrap("https://post.chikka.com/smsapi/request")


def key(*a):
  return ":".join(["mmsms"] + map(str, a))


def send(num, msg):
  msg_id = str(simpleflake())
  res = chikka.post(data=dict(
    message_type="SEND",
    mobile_number=num,
    shortcode=app.config["CHIKKA_SHORTCODE"],
    message_id=msg_id,
    message=msg,
    client_id=app.config["CHIKKA_CLIENT_ID"],
    secret_key=app.config["CHIKKA_SECRET_KEY"],
  ))
  is_ok = res.status == 200
  if is_ok:
    db.sadd(key("sent"), ":".join([
      msg_id,
      num,
      msg,
    ]))
  return is_ok


@app.route("/", methods=["GET", "POST"])
def index():
  if request.method == "POST":
    names = request.form.getlist("name")
    numbers = request.form.getlist("number")
    pot = filter(
      lambda x: all(map(bool, x)),
      zip(names, numbers),
    )
    random.shuffle(pot)
    for i, giver in enumerate(pot):
      rcvr = pot[(i + 1) % len(pot)]
      send(giver[1], """Hi {},

You drew {}!

mmsms -""".format(giver[0], rcvr[0]))
  return render_template("index.html")


if __name__ == '__main__':
  app.run(host="0.0.0.0", port=5000, debug=True)

