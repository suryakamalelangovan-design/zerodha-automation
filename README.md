# Zerodha Kite Connect — Read-only Dashboard

A small local web dashboard built with **FastAPI**, HTML, CSS and JavaScript. It uses the official `kiteconnect` Python client and the Kite Connect v3 API.

## What it does

- Connects through the official Zerodha Kite login page.
- Exchanges the callback `request_token` for an access token on the Python server.
- Displays profile, equity/commodity funds and margins, net/day positions, holdings, today's orders and today's trades.
- Refreshes data on demand.
- Keeps API credentials and access tokens out of browser JavaScript.

**Read-only scope:** this project intentionally contains no order placement, modification, cancellation, position conversion, or trading-strategy code. The orders and trades shown are retrieved using GET endpoints.

## Requirements

- Windows 10/11
- Python 3.10 or newer (3.11/3.12 recommended)
- Active Zerodha account and Kite Connect app/API credentials
- Internet connection for Zerodha authentication and API requests

## 1. Configure your Kite Connect app

In the Zerodha Kite Connect developer console, create/open your app and set its registered redirect URL to exactly:

`http://127.0.0.1:8000/callback`

Use `127.0.0.1` consistently. Do not switch between `localhost` and `127.0.0.1` unless you also update the registered redirect URL.

## 2. Set up the project on Windows

Open **Command Prompt** or **PowerShell**, then move into this project folder:

```powershell
cd path\to\zerodha_kite_readonly
```

Create and activate a virtual environment:

```powershell
py -3 -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create your local environment file:

```powershell
copy .env.example .env
notepad .env
```

Fill in `KITE_API_KEY` and `KITE_API_SECRET` in `.env` on your own computer. Do **not** paste them into chat, commit `.env` to Git, or put them in frontend files.

Generate a strong session secret in PowerShell:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the generated value into `SESSION_SECRET` in `.env`. Keep `COOKIE_SECURE=false` for this HTTP-only localhost setup. For a properly configured HTTPS deployment, set it to `true`.

## 3. Run the dashboard

With the virtual environment activated:

```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Open this exact address in your browser:

`http://127.0.0.1:8000`

Click **Connect to Zerodha**. The browser will open the official Zerodha Kite login page. Complete the normal Zerodha login and 2FA process there. Zerodha redirects to the registered local callback and the server completes the token exchange.

After connection, use **Refresh** to reload the account data.

To stop the server, return to the terminal and press `Ctrl+C`.

## 4. Daily use and session behavior

- Kite access tokens normally expire at 6:00 AM the following day or can be invalidated by a master logout.
- This app keeps the access token in server process memory only. It is not written to a file or sent to the browser.
- Restarting the app clears the in-memory token; connect again.
- The browser receives only a signed, HTTP-only session cookie containing a random session identifier, not the Kite access token.
- **Disconnect** clears this app's local session/token. It does not log you out of Zerodha's Kite web/mobile apps or revoke the API token at Zerodha.
- This starter app is designed for one local user and one running server process. Do not expose it to the public internet. Multi-worker hosting would need a shared server-side session store and additional deployment hardening.

## 5. Troubleshooting

**“Add KITE_API_KEY…”**
- Check that `.env` exists in the same folder as `main.py`.
- Confirm the variable names are exact and values have no surrounding quotes/spaces.
- Restart Uvicorn after editing `.env`.

**Redirect URL mismatch**
- Confirm the developer console redirect URL is exactly `http://127.0.0.1:8000/callback`.
- Open the dashboard using `http://127.0.0.1:8000`, not `localhost`.

**Authentication/state check failed**
- Start from the dashboard's Connect button; do not reuse an old callback URL.
- Allow cookies for `127.0.0.1`.
- Check your system clock and verify the correct app's API key is in `.env`.

**Token/session expired**
- Click Connect to Zerodha again. Kite access tokens expire daily and can also be invalidated by a master logout.

**Port 8000 already in use**
- Stop the other process using port 8000. The callback URL registered with Zerodha must match the port, so do not change it casually.

**No orders/trades shown**
- The dashboard filters the returned order/trade book to the current date in India Standard Time (IST). It can be empty on a non-trading day or when there was no activity.

## Security notes

- Never share your API secret, request token, access token, password, PIN or TOTP with anyone.
- `.env` is excluded by `.gitignore`; keep it private.
- Uvicorn is started with `--no-access-log` because the callback URL includes a short-lived `request_token` query parameter. Avoid enabling request URL logging for this local app.
- The session token store is in-memory. It is intentionally simple for a local proof of concept, not a production session-management system.
- Only run this app on your own machine. The server binds to `127.0.0.1`, not all network interfaces.

## API references

- [Kite Connect v3 documentation](https://kite.trade/docs/connect/v3/)
- [User, login flow, profile and margins](https://kite.trade/docs/connect/v3/user/)
- [Portfolio: holdings and positions](https://kite.trade/docs/connect/v3/portfolio/)
- [Orders and trades](https://kite.trade/docs/connect/v3/orders/)

## Project structure

```text
zerodha_kite_readonly/
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── templates/
│   └── index.html
└── static/
    ├── app.js
    └── styles.css
```
