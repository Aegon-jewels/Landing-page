import threading
import time

_lock = threading.Lock()
_expires_at: float | None = None  # Unix timestamp (ms) when timer ends

def start_timer(expires_at_ms: float):
    global _expires_at
    with _lock:
        _expires_at = expires_at_ms
    print(f'[Timer] Started. Ends at {time.strftime("%H:%M:%S", time.localtime(expires_at_ms / 1000))}')

def stop_timer():
    global _expires_at
    with _lock:
        _expires_at = None
    print('[Timer] Stopped.')

def get_timer_status() -> dict:
    with _lock:
        exp = _expires_at
    now_ms = time.time() * 1000
    if exp and now_ms < exp:
        seconds_left = int((exp - now_ms) / 1000)
        return {'running': True, 'secondsLeft': seconds_left}
    return {'running': False, 'secondsLeft': 0}
