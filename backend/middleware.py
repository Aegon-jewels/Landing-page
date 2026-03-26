import time
from store.config_store import get_config

_blocked: dict[str, float] = {}  # ip -> blocked_at timestamp (seconds)

def _get_block_duration_seconds() -> float:
    cfg = get_config()
    minutes = cfg.get('blockDurationMinutes', 15)
    return float(minutes) * 60

def block_user(ip: str):
    _blocked[ip] = time.time()
    _cleanup()

def is_blocked(ip: str) -> bool:
    blocked_at = _blocked.get(ip)
    if blocked_at is None:
        return False
    return time.time() < blocked_at + _get_block_duration_seconds()

def _cleanup():
    duration = _get_block_duration_seconds()
    now = time.time()
    expired = [k for k, v in _blocked.items() if now - v > duration]
    for k in expired:
        del _blocked[k]
