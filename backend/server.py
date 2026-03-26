import os
import sys
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
CORS(app, supports_credentials=True)

from store.config_store import get_config, save_config
from store.prediction_store import get_all, get_by_period, get_pending
from auth import auth_required, check_login, create_token
from timer import get_timer_status
from middleware import is_blocked, block_user
from predictor import start_predictor

# ── Auth routes ──────────────────────────────────────────────────────────────
@app.route('/user/login', methods=['POST'])
def login():
    body = request.get_json() or {}
    username = body.get('username', '')
    password = body.get('password', '')
    if not check_login(username, password):
        return jsonify({'error': 'Invalid username or password'}), 401
    token = create_token(username)
    resp = jsonify({'token': token})
    resp.set_cookie('token', token, httponly=True, samesite='Lax', max_age=43200)
    return resp

@app.route('/user/logout', methods=['POST'])
def logout():
    resp = jsonify({'message': 'Logged out'})
    resp.delete_cookie('token')
    return resp

# ── Config routes ─────────────────────────────────────────────────────────────
@app.route('/config/fetch-configs', methods=['GET'])
def fetch_configs():
    return jsonify(get_config())

@app.route('/config/save-configs', methods=['POST'])
@auth_required
def save_configs():
    payload = request.get_json() or {}
    updated = save_config(payload)
    return jsonify({'success': True, 'message': 'Config saved', 'data': updated})

@app.route('/config/apply-configs', methods=['POST'])
@auth_required
def apply_configs():
    payload = request.get_json() or {}
    updated = save_config(payload)
    return jsonify({'success': True, 'message': 'Config applied', 'data': updated})

# ── Prediction routes ─────────────────────────────────────────────────────────
@app.route('/predictions', methods=['GET'])
def predictions():
    ip = request.remote_addr
    if is_blocked(ip):
        return jsonify({'error': 'Access blocked due to WIN status'}), 403
    data = get_all(5)
    return jsonify(data)

@app.route('/predictions/pending', methods=['GET'])
def pending_prediction():
    item = get_pending()
    return jsonify(item)

@app.route('/predictions/status/<period_id>', methods=['GET'])
def prediction_status(period_id):
    ip = request.remote_addr
    if is_blocked(ip):
        return jsonify({'error': 'Access blocked due to WIN status'}), 403
    item = get_by_period(period_id)
    if not item:
        return jsonify({'error': 'Prediction not found'}), 404
    if item['status'] == 'WIN':
        block_user(ip)
    return jsonify(item)

# ── Timer route ───────────────────────────────────────────────────────────────
@app.route('/timer', methods=['GET'])
def timer_status():
    return jsonify(get_timer_status())

# ── Serve React frontend ──────────────────────────────────────────────────────
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    dist = os.path.join(app.root_path, '..', 'frontend', 'dist')
    full = os.path.join(dist, path)
    if path and os.path.exists(full):
        return send_from_directory(dist, path)
    return send_from_directory(dist, 'index.html')

# ── Start ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    start_predictor()
    port = int(os.getenv('PORT', 5000))
    print(f'[Server] Running at http://localhost:{port}')
    app.run(host='0.0.0.0', port=port, debug=False)
