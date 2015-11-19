import os
import random

from flask import Flask, render_template, request
from redis import StrictRedis

app = Flask(__name__)
db = StrictRedis(host=os.environ.get('REDIS_HOST', 'localhost'))


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        names = request.form.getlist('name')
        numbers = request.form.getlist('number')
        theme = request.form.get('theme', '').strip()
        db.sadd('themes', theme)  # For stats purposes :)
        members = zip(names, numbers)
        random.shuffle(members)
        for i, [name, number] in enumerate(members):
            assigned_name, _ = members[(i + 1) % len(members)]
            message = "Hi, {}. You drew {} for our Monito-monita! ".format(
                name, assigned_name)
            if theme:
                message += 'Our theme is "{}" '
            print message
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
