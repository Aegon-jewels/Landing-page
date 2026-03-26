import json
import os
from threading import Lock
from datetime import datetime

PREDICTIONS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'predictions.json')
_lock = Lock()

def _ensure_file():
    os.makedirs(os.path.dirname(PREDICTIONS_PATH), exist_ok=True)
    if not os.path.exists(PREDICTIONS_PATH):
        with open(PREDICTIONS_PATH, 'w') as f:
            json.dump([], f)

def _read() -> list:
    _ensure_file()
    with open(PREDICTIONS_PATH, 'r') as f:
        return json.load(f)

def _write(data: list):
    with open(PREDICTIONS_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def get_all(limit: int = 5) -> list:
    with _lock:
        data = _read()
    # Return last N, sorted by createdAt ascending (oldest first for display)
    return data[-limit:] if len(data) > limit else data

def get_by_period(period_id: str) -> dict | None:
    with _lock:
        data = _read()
    for item in reversed(data):
        if item['periodId'] == period_id:
            return item
    return None

def create_prediction(period_id: str, prediction: str) -> dict:
    record = {
        'periodId': period_id,
        'prediction': prediction,
        'status': 'PENDING',
        'actualResult': None,
        'createdAt': datetime.utcnow().isoformat()
    }
    with _lock:
        data = _read()
        # Avoid duplicates
        for item in data:
            if item['periodId'] == period_id:
                return item
        data.append(record)
        # Keep only last 100 records to avoid file bloat
        if len(data) > 100:
            data = data[-100:]
        _write(data)
    return record

def update_prediction(period_id: str, status: str, actual_result: str = None) -> dict | None:
    with _lock:
        data = _read()
        for item in data:
            if item['periodId'] == period_id:
                item['status'] = status
                if actual_result:
                    item['actualResult'] = actual_result
                _write(data)
                return item
    return None

def get_pending() -> dict | None:
    with _lock:
        data = _read()
    for item in reversed(data):
        if item['status'] == 'PENDING':
            return item
    return None
