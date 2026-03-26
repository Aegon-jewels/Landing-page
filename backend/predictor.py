import time
import threading
import requests
from store.prediction_store import (
    create_prediction, update_prediction, get_all
)
from store.config_store import get_config
from timer import start_timer, stop_timer

API_URL = 'https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json'
HEADERS = {
    'sec-ch-ua-platform': '"Windows"',
    'Referer': 'https://tashanwin.in/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
}

_predictor_thread: threading.Thread | None = None


def number_to_bs(num: int) -> str:
    return 'BIG' if num >= 5 else 'SMALL'


def fetch_latest_data() -> list | None:
    try:
        resp = requests.get(API_URL, params={'ts': str(int(time.time() * 1000))}, headers=HEADERS, timeout=10)
        items = resp.json().get('data', {}).get('list', [])
        return list(reversed(items))
    except Exception as e:
        print(f'[Predictor] API Error: {e}')
        return None


def get_stable_prediction(bs_sequence: list) -> dict:
    if len(bs_sequence) < 5:
        return {'prediction': None, 'reason': 'Not enough data'}

    # Check 5+ in a row
    for val in ['SMALL', 'BIG']:
        count = 0
        for v in reversed(bs_sequence):
            if v == val:
                count += 1
            else:
                break
        if count >= 5:
            return {'prediction': val, 'reason': f'{count} in a row'}

    last3 = bs_sequence[-3:]
    patterns3 = {
        ('BIG', 'BIG', 'SMALL'): 'SMALL',
        ('SMALL', 'SMALL', 'BIG'): 'BIG',
        ('SMALL', 'BIG', 'BIG'): 'SMALL',
        ('BIG', 'SMALL', 'SMALL'): 'BIG',
    }
    key3 = tuple(last3)
    if key3 in patterns3:
        return {'prediction': patterns3[key3], 'reason': f'Override {" ".join(key3)}'}

    last4 = bs_sequence[-4:]
    patterns4 = {
        ('SMALL', 'BIG', 'BIG', 'BIG'): 'SMALL',
        ('BIG', 'SMALL', 'SMALL', 'SMALL'): 'BIG',
    }
    key4 = tuple(last4)
    if key4 in patterns4:
        return {'prediction': patterns4[key4], 'reason': f'Override {" ".join(key4)}'}

    return {'prediction': bs_sequence[-1], 'reason': 'Fallback'}


def get_next_period_id(current_pid: str) -> str:
    pid = current_pid.lstrip('0') or '0'
    date_part = current_pid[:8]
    prefix = current_pid[8:13]
    minute = int(current_pid[-4:])
    if minute < 1440:
        return f"{date_part}{prefix}{str(minute + 1).zfill(4)}"
    else:
        from datetime import datetime, timedelta
        dt = datetime(int(date_part[:4]), int(date_part[4:6]), int(date_part[6:8]))
        dt = dt + timedelta(days=1)
        new_date = dt.strftime('%Y%m%d')
        return f"{new_date}{prefix}0001"


def run_prediction_loop():
    """Single cycle: runs until a WIN is found, then returns."""
    bet_pending = False
    last_prediction_issue = None
    last_prediction = None

    stop_timer()

    while True:
        data_list = fetch_latest_data()
        if not data_list or len(data_list) < 10:
            time.sleep(5)
            continue

        latest10 = data_list[-10:]
        global_history = [number_to_bs(int(item['number'])) for item in latest10]
        last_result = data_list[-1]
        current_issue = last_result['issueNumber']

        if bet_pending:
            bet_result_item = next(
                (item for item in data_list if item['issueNumber'] == last_prediction_issue), None
            )
            if bet_result_item:
                actual_bs = number_to_bs(int(bet_result_item['number']))
                win = actual_bs == last_prediction
                status = 'WIN' if win else 'LOSS'

                print(f'[Predictor] Period: {last_prediction_issue} | Prediction: {last_prediction} | Status: {status}')

                update_prediction(last_prediction_issue, status, actual_bs)

                if win:
                    return  # WIN found — exit loop
                bet_pending = False
            else:
                time.sleep(10)
                continue

        last_prediction_issue = get_next_period_id(current_issue)
        result = get_stable_prediction(global_history)
        last_prediction = result['prediction']
        bet_pending = True

        print(f'[Predictor] Next Period: {last_prediction_issue} | Bet: {last_prediction} | PENDING')
        create_prediction(last_prediction_issue, last_prediction)
        time.sleep(10)


def scheduler_loop():
    """Outer loop: run prediction until WIN, sleep timer, repeat."""
    while True:
        run_prediction_loop()

        cfg = get_config()
        minutes = cfg.get('timerDurationForNextPrediction', 2)
        duration_ms = minutes * 60 * 1000
        expires_at = time.time() * 1000 + duration_ms

        print(f'[Predictor] WIN! Sleeping {minutes} min before next cycle.')
        start_timer(expires_at)
        time.sleep(minutes * 60)
        stop_timer()


def start_predictor():
    global _predictor_thread
    if _predictor_thread and _predictor_thread.is_alive():
        return
    _predictor_thread = threading.Thread(target=scheduler_loop, daemon=True)
    _predictor_thread.start()
    print('[Predictor] Background thread started.')
