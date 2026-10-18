from flask import Flask
from flask import request
from flask import jsonify

from events import (
    add_event,
    get_events
)

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    add_event(data)

    print("\nNOVO EVENTO RECEBIDO")
    print(data)

    return jsonify({
        "status": "ok"
    })


@app.route("/events")
def events():

    return jsonify(
        get_events()
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )