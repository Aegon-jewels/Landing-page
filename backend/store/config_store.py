import json
import os
from threading import Lock

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'config.json')
_lock = Lock()

DEFAULT_CONFIG = {
    "appName": "OK WIN WINGO",
    "environment": "production",
    "version": "1.0.0",
    "mailTo": "",
    "maintenanceMode": False,
    "blockDurationMinutes": 15,
    "timerDurationForNextPrediction": 2,
    "topButtons": [],
    "menuItems": [
        {"id": "1", "name": "Home", "href": "/"},
        {"id": "2", "name": "Admin", "href": "/admin"}
    ],
    "bannerImage": {"image": ""},
    "howToParticipate": {"title": "How to Participate", "description": ""},
    "registrationTutorial": {"buttonName": "Register Now", "buttonHref": "#", "description": ""},
    "loginTutorial": {"buttonName": "Login Now", "buttonHref": "#", "description": ""},
    "aboutOkWin": {"title": "About OK Win", "description": ""},
    "feedback": {"images": [], "description": ""},
    "giftCode": {"title": "Gift Code", "code": "", "description": ""},
    "earningRealMoney": {"title": "Earning Real Money", "referralCode": "", "description": ""},
    "winPopup": {
        "enabled": True,
        "message": "\U0001f389 Congratulations! You got a WIN!",
        "subMessage": "Please join our channel for more wins!",
        "channelButtonText": "Join Channel",
        "channelLink": "",
        "closeButtonDelaySeconds": 7
    }
}

def _ensure_file():
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)

def get_config() -> dict:
    _ensure_file()
    with _lock:
        with open(CONFIG_PATH, 'r') as f:
            data = json.load(f)
    # Deep merge with defaults so new fields always exist
    merged = dict(DEFAULT_CONFIG)
    merged.update(data)
    # Nested merges
    for key in ['bannerImage', 'howToParticipate', 'registrationTutorial',
                'loginTutorial', 'aboutOkWin', 'feedback', 'giftCode',
                'earningRealMoney', 'winPopup']:
        if isinstance(DEFAULT_CONFIG.get(key), dict):
            merged[key] = {**DEFAULT_CONFIG[key], **data.get(key, {})}
    return merged

def save_config(payload: dict) -> dict:
    _ensure_file()
    current = get_config()
    # Deep merge incoming payload into current config
    for key, value in payload.items():
        if isinstance(value, dict) and isinstance(current.get(key), dict):
            current[key] = {**current[key], **value}
        else:
            current[key] = value
    with _lock:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(current, f, indent=2)
    return current
