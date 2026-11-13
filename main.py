import hashlib
import hmac
import os
import secrets
import sys
import threading
import webbrowser
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from kiteconnect import KiteConnect, KiteException

APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
load_dotenv(APP_DIR / ".env")

BASE_DIR = RESOURCE_DIR
API_KEY = os.getenv("KITE_API_KEY", "").strip()
API_SECRET = os.getenv("KITE_API_SECRET", "").strip()
CALLBACK_URL = os.getenv("KITE_REDIRECT_URL", "http://127.0.0.1:8000/callback").strip()
SESSION_SECRET = os.getenv("SESSION_SECRET", "").strip()
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
IST = ZoneInfo("Asia/Kolkata")

if not SESSION_SECRET:
    raise RuntimeError("SESSION_SECRET is missing. Copy .env.example to .env and set a random SESSION_SECRET.")

app = FastAPI(title="Zerodha Read-only Dashboard")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="zkd_session",
    same_site="lax",
    https_only=COOKIE_SECURE,
    max_age=8 * 60 * 60,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Access tokens and OAuth state stay server-side, in process memory only.
# Restarting the app clears them; sign in again after a restart.
token_store: dict[str, str] = {}


def kite_client(access_token: str | None = None) -> KiteConnect:
    if not API_KEY or not API_SECRET:
        raise RuntimeError("KITE_API_KEY or KITE_API_SECRET is missing in .env.")
    kite = KiteConnect(api_key=API_KEY)
    if access_token:
        kite.set_access_token(access_token)
    return kite


def session_id(request: Request) -> str:
    sid = request.session.get("sid")
    if not sid:
        sid = secrets.token_urlsafe(32)
        request.session["sid"] = sid
    return sid


def current_client(request: Request) -> KiteConnect:
    sid = request.session.get("sid")
    access_token = token_store.get(sid or "")
    if not access_token:
        raise PermissionError("Not connected. Click Connect to Zerodha and complete login.")
    return kite_client(access_token)


def today_ist() -> date:
    return datetime.now(IST).date()


def record_date(record: dict) -> date | None:
    # Kite order/trade records may expose one of these timestamp fields.
    for key in ("order_timestamp", "exchange_timestamp", " fill_timestamp", "trade_timestamp"):
        value = record.get(key.strip())
        if not value:
            continue
        try:
            if isinstance(value, datetime):
                dt = value
            else:
                dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=IST)
            return dt.astimezone(IST).date()
        except (ValueError, TypeError):
            continue
    return None


@app.get("/", response_class=HTMLResponse)
async def home():
    return (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")


@app.get("/connect")
async def connect(request: Request):
    if not API_KEY or not API_SECRET:
        return RedirectResponse("/?setup_error=credentials", status_code=303)
    sid = session_id(request)
    state = secrets.token_urlsafe(24)
    request.session["oauth_state"] = state
    request.session["oauth_started"] = True
    login_url = (
        "https://kite.zerodha.com/connect/login?v=3&"
        + urlencode({"api_key": API_KEY, "redirect_params": urlencode({"state": state})})
    )
    return RedirectResponse(login_url, status_code=302)


@app.get("/callback", response_class=HTMLResponse)
async def callback(request: Request, request_token: str | None = None,
                   status: str | None = None, state: str | None = None):
    expected_state = request.session.get("oauth_state")
    request.session.pop("oauth_state", None)
    request.session.pop("oauth_started", None)

    if status == " ಬಹ":
        return RedirectResponse("/?error=login_cancelled", status_code=303)
    if not request_token:
        return RedirectResponse("/?error=missing_request_token", status_code=303)
    if not expected_state or not state or not hmac.compare_digest(str(expected_state), str(state)):
        return RedirectResponse("/?error=state_check_failed", status_code=303)

    try:
        data = kite_client().generate_session(request_token, api_secret=API_SECRET)
        sid = session_id(request)
        token_store[sid] = data["access_token"]
        request.session["connected"] = True
        return RedirectResponse("/?connected=1", status_code=303)
    except Exception as exc:
        # Avoid returning request tokens, API secrets, or access tokens to the browser.
        message = "Authentication failed. Check your Kite app settings and try again."
        if isinstance(exc, KiteException):
            message = f"Zerodha authentication failed: {exc}"
        return RedirectResponse("/?error=auth_failed&detail=" + urlencode({"message": message})[8:], status_code=303)


@app.get("/api/status")
async def api_status(request: Request):
    sid = request.session.get("sid")
    return {"connected": bool(sid and token_store.get(sid))}


@app.get("/api/dashboard")
async def dashboard(request: Request):
    try:
        kite = current_client(request)
        profile = kite.profile()
        margins = kite.margins()
        positions = kite.positions()
        holdings = kite.holdings()
        all_orders = kite.orders()
        all_trades = kite.trades()
        today = today_ist()
        orders_today = [x for x in all_orders if record_date(x) == today]
        trades_today = [x for x in all_trades if record_date(x) == today]
        return {
            "profile": profile,
            "margins": margins,
            "positions": positions,
            "holdings": holdings,
            "orders_today": orders_today,
            "trades_today": trades_today,
            "as_of": datetime.now(IST).isoformat(),
        }
    except PermissionError as exc:
        return JSONResponse({"error": str(exc)}, status_code=401)
    except KiteException as exc:
        message = str(exc)
        status_code = 401 if "token" in message.lower() or "session" in message.lower() else 502
        return JSONResponse({"error": f"Zerodha API error: {message}"}, status_code=status_code)
    except Exception:
        return JSONResponse(
            {"error": "Could not load account data. Check the server console and your connection."},
            status_code=500,
        )


@app.post("/api/logout")
async def logout(request: Request):
    sid = request.session.get("sid")
    if sid:
        token_store.pop(sid, None)
    request.session.clear()
    return {"ok": True}


@app.get("/health")
async def health():
    return {"ok": True, "read_only": True}


if __name__ == "__main__":
    import uvicorn
    threading.Timer(1.8, lambda: webbrowser.open("http://127.0.0.1:8000")).start()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning", access_log=False)
