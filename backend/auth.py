import os
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify
from store.config_store import get_config, save_config

JWT_SECRET = os.getenv('JWT_SECRET', 'supersecretkey_change_me')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

def _get_admin_creds():
    """Admin creds: env vars take priority, else fall back to config.json"""
    cfg = get_config()
    username = os.getenv('ADMIN_USERNAME') or cfg.get('adminUsername', 'admin')
    password = os.getenv('ADMIN_PASSWORD') or cfg.get('adminPassword', 'admin123')
    return username, password

def create_token(username: str) -> str:
    payload = {
        'username': username,
        'role': 'admin',
        'exp': datetime.now(timezone.utc) + timedelta(hours=12)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Cookie first
        token = request.cookies.get('token')
        # Then Authorization header
        if not token:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
        if not token:
            return jsonify({'error': 'Token required'}), 401
        decoded = verify_token(token)
        if not decoded:
            return jsonify({'error': 'Invalid or expired token'}), 403
        request.user = decoded
        return f(*args, **kwargs)
    return decorated

def check_login(username: str, password: str) -> bool:
    valid_user, valid_pass = _get_admin_creds()
    return username == valid_user and password == valid_pass
