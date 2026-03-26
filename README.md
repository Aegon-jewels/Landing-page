# Landing Page — WinGo Prediction

Full-stack prediction landing page.
- **Backend**: Python Flask + JSON flat file storage (no MongoDB, no Redis)
- **Frontend**: React + Vite + Tailwind CSS (mobile-first)

---

## Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your JWT_SECRET, ADMIN_USERNAME, ADMIN_PASSWORD
python server.py
```

### Frontend
```bash
cd frontend
npm install
npm run build
# Or for dev:
npm run dev
```

### One command (production)
```bash
# Build frontend first
cd frontend && npm run build && cd ..
# Start backend (serves built frontend too)
cd backend && python server.py
```

---

## Admin Panel
Go to `/admin` — login with the credentials set in `.env`

All settings are stored in `backend/data/config.json`

---

## API Endpoints
| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| POST | `/user/login` | No | Admin login |
| POST | `/user/logout` | No | Logout |
| GET | `/config/fetch-configs` | No | Get all config |
| POST | `/config/save-configs` | Yes | Save config |
| POST | `/config/apply-configs` | Yes | Apply config |
| GET | `/predictions` | No | Get last 5 predictions |
| GET | `/predictions/status/:id` | No | Get status by period ID |
| GET | `/timer` | No | Get timer status |

---

## Data Storage
- `backend/data/config.json` — all site config, admin creds, win popup settings
- `backend/data/predictions.json` — prediction history (auto-trimmed to 100 records)

## Prediction Algorithm
Exact same logic as original:
- Fetches WinGo 1M history from `draw.ar-lottery01.com`
- BIG/SMALL prediction using pattern matching (5-in-a-row, BBS, SSB, SBB, BSS overrides)
- Loops until WIN, then triggers timer, then restarts
