from datetime import timedelta

import requests


def should_send(last_sent, now, cooldown_hours):
    return last_sent is None or (now - last_sent) >= timedelta(hours=cooldown_hours)


def post_slack(webhook, text):
    resp = requests.post(webhook, json={"text": text}, timeout=10)
    resp.raise_for_status()
