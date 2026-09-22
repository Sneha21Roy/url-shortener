# URL Shortener

A Flask-based URL shortener with click tracking, an analytics dashboard,
QR code generation, and JWT-based user authentication.

## Features

- **Generate short URLs** — random 6-char codes, or a custom alias
- **Track clicks** — every redirect logs timestamp, IP, user agent, referrer
- **Analytics dashboard** — total clicks, clicks-per-day chart, top referrers
- **Bonus: QR code generation** — PNG QR code for any short link
- **Bonus: User authentication** — JWT-based register/login; anonymous
  shortening is also supported (like most public shorteners)

## Project structure

```
url-shortener/
├── app.py                     # Flask application factory + entry point
├── config.py                  # App configuration (from environment)
├── extensions.py              # Shared db / jwt instances
├── models.py                  # SQLAlchemy models: User, URL, Click
├── utils.py                   # Short code generation, URL validation, QR codes
├── routes/
│   ├── auth_routes.py         # /api/auth/* - register, login, me
│   ├── url_routes.py          # /api/shorten, /api/urls, /<short_code> redirect
│   └── analytics_routes.py    # /api/analytics/<code>, /api/qr/<code>
├── templates/
│   └── dashboard.html         # Single-page dashboard UI (vanilla JS + Chart.js)
├── requirements.txt
├── .env.example
└── README.md
```

## Database schema

```
User (1) ----< (many) URL (1) ----< (many) Click
```

- **User**: id, username, email, password_hash, created_at
- **URL**: id, short_code (unique), original_url, owner_id (nullable FK →
  User — anonymous links are allowed), created_at, expires_at, is_active
- **Click**: id, url_id (FK → URL), clicked_at, ip_address, user_agent, referrer

Click counts and analytics are computed from the `Click` table on demand,
rather than a running counter column, so they can never drift out of sync
and can support richer breakdowns (by day, by referrer, etc.) for free.

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **(Optional) Configure environment** — copy `.env.example` to `.env` and
   adjust if needed. Sensible defaults are used if you skip this step
   (SQLite database, dev secret keys).

3. **Run the app**:
   ```bash
   python app.py
   ```
   Open http://localhost:5000 for the dashboard.

## API reference

### Auth
| Method | Endpoint | Body | Auth |
|---|---|---|---|
| POST | `/api/auth/register` | `{username, email, password}` | — |
| POST | `/api/auth/login` | `{email, password}` | — |
| GET | `/api/auth/me` | — | Bearer token |

### URLs
| Method | Endpoint | Body | Auth |
|---|---|---|---|
| POST | `/api/shorten` | `{original_url, custom_alias?, expires_at?}` | Optional (links to your account if logged in) |
| GET | `/api/urls` | — | Required |
| DELETE | `/api/urls/<short_code>` | — | Required (must own the URL) |
| GET | `/<short_code>` | — | — (public redirect, logs a click) |

### Analytics & QR
| Method | Endpoint | Auth |
|---|---|---|
| GET | `/api/analytics/<short_code>` | Public for anonymous links, owner-only for account-linked links |
| GET | `/api/qr/<short_code>` | — (returns a PNG image) |

### Example: shorten a URL with curl
```bash
curl -X POST http://localhost:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com/some/very/long/path"}'
```

### Example: register + shorten as a logged-in user
```bash
# 1. Register and grab the token
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"sneha","email":"sneha@example.com","password":"secret123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Shorten a URL linked to that account
curl -X POST http://localhost:5000/api/shorten \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"original_url": "https://example.com", "custom_alias": "mylink"}'
```

## How it works

1. **Shortening**: `POST /api/shorten` validates the URL, generates (or
   accepts) a short code, and stores it. If a valid JWT is present, the
   link is associated with that user; otherwise it's anonymous.
2. **Redirecting**: `GET /<short_code>` looks up the code, logs a `Click`
   row (timestamp, IP, user agent, referrer), and issues an HTTP redirect
   to the original URL.
3. **Analytics**: `GET /api/analytics/<short_code>` aggregates the `Click`
   rows for that URL into a total count, a 14-day daily series (for the
   dashboard's line chart), and a top-referrers breakdown.
4. **QR codes**: `GET /api/qr/<short_code>` generates a PNG QR code
   on the fly encoding the short link, using the `qrcode` library.
5. **Auth**: Flask-JWT-Extended issues a signed access token on
   register/login, which the dashboard stores in `localStorage` and sends
   as a `Bearer` token on subsequent requests.

## Possible extensions

- Rate limiting on `/api/shorten` to prevent abuse
- Password reset flow
- Per-URL password protection
- Geolocation of clicks (via IP lookup) for a richer analytics dashboard
- Swap SQLite for PostgreSQL in `DATABASE_URL` for production use
