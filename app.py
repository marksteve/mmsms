from flask import (
  Flask,
  request,
)
from simpleflake import simpleflake
import json
import random
import redis
import requests


SHORTCODE = "21589973"


fl = Flask(__name__)
db = redis.StrictRedis()


def key(*a):
  return ":".join(map(str, a))


def get_user_token(user_id):
  return db.get(key("users", user_id))


def send(user, message):
  sender = SHORTCODE[-4:]
  access_token = get_user_token(user)
  params = dict(access_token=access_token)
  payload = json.dumps(dict(
    outboundSMSMessageRequest=dict(
    clientCorrelator=simpleflake(),
    senderAddress="tel:%s" % sender,
    outboundSMSTextMessage=dict(message=message),
    address=["tel:+63%s" % user],
  )))
  # TODO: Check response
  requests.post(
    "http://devapi.globelabs.com.ph/smsmessaging/v1/outbound/%s/requests" % sender,
    headers={"Content-Type": "application/json"},
    params=params,
    data=payload,
  )


@fl.route("/subscribe", methods=["GET"])
def subscribe():
  u = request.args["subscriber_number"]
  k = key("users", u)
  # Set user access token
  db.set(k, request.args["access_token"])
  return ""


@fl.route("/receive", methods=["POST"])
def receive():
  for m in request.json["inboundSMSMessageList"]["inboundSMSMessage"]:
    s = m["message"].strip().upper().split(" ")
    num = m["senderAddress"].replace("tel:+63", "")

    if s[0] == "CREATE":
      while True:
        id = str(simpleflake())[:6]
        if db.exists(id):
          continue
        break
      db.set(key("mmowners", id), num)
      send(
        num,
        (
          "Game! Make participants subscribe to %s as well.\n\n"
          "Join by sending\nJOIN %s <NAME>\n\n"
          "Draw by sending\nDRAW %s"
        ) % (
          SHORTCODE,
          id,
          id,
        )
      )

    if s[0] == "JOIN":
      id = s[1]
      name = s[2]
      o = db.get(key("mmowners", id))
      db.sadd(key("mmgroups", id), key(num, name))
      send(o, "%s (%s) has joined!" % num, name)

    if s[0] == "DRAW":
      o = db.get(key("mmowners", id))
      if num != o:
        abort(403)
      g = [db.smembers(key("mmgroups", id))]
      ordered = []
      while g:
        m = random.choice(g)
        g.remove(m)
        ordered.append(m)
      ol = len(ordered)
      ordered.append(ordered[0])
      for i, m in enumerate(ordered):
        num, name = m.split(":", 1)
        pnum, pname = ordered[i + 1].split(":", 1)
        send(num, "You're MONITO MONITA is %s!", pname)
        if i >= ol - 1:
          break

    break
  return ""


def main():
  fl.run(host="0.0.0.0", port=6000, debug=True)


if __name__ == '__main__':
  main()

