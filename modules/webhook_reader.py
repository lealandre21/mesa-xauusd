import requests


def get_webhook_events():

    try:

        response = requests.get(
            "http://127.0.0.1:5000/events",
            timeout=2
        )

        return response.json()

    except Exception:

        return []