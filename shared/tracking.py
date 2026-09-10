"""
THIS FILE IS CALLED TRACKING.PY
ALL THIS DOES IS CREATE A UNIQUE ID FOR EACH USER
AND PING MY SERVER UPON LAUNCH, SO I CAN TRACK USER AMOUNT
AND USER USAGE AMOUNT FOR MY RESUMES.

THIS IS COMPLETELY ANONYMOUS, NO PERSONAL DATA COLLECTED.
"""
import json
import platform
import threading
import uuid
from pathlib import Path

import requests
from platformdirs import user_data_dir

APP_NAME = "RaidTools"
APP_VERSION = "1.1.0"
TRACKER_URL = "https://tracker.lxghtend.xyz/ping"

CONFIG_DIR = Path(user_data_dir(APP_NAME))
CONFIG_FILE = CONFIG_DIR / "install_id.json"


def get_or_create_install_id() -> str:
    """Returns a persistent anonymous ID for this install, creating one if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            return data["install_id"]
        except (json.JSONDecodeError, KeyError):
            pass  # fall through and regenerate

    new_id = str(uuid.uuid4())
    CONFIG_FILE.write_text(json.dumps({"install_id": new_id}))
    return new_id


def _do_send_ping():
    try:
        payload = {
            "uuid": get_or_create_install_id(),
            "app_version": APP_VERSION,
            "os": f"{platform.system()} {platform.release()}",
        }
        requests.post(TRACKER_URL, json=payload, timeout=3)
    except requests.RequestException:
        pass # silent fail


def send_ping():
    """Fire-and-forget: sends the ping on a background thread so app startup never blocks."""
    threading.Thread(target=_do_send_ping, daemon=True).start()
