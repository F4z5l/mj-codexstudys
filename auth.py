"""
auth.py  –  Auth pool (seed accounts + dynamic user accounts from Redis)
"""

import json
import random
import requests
from upstash_redis import Redis
from config import (
    REDIS_URL, REDIS_TOKEN, SEED_ACCOUNTS,
    BASE_URL, COMMON_HEADERS, TOKEN_TTL
)

redis = Redis(url=REDIS_URL, token=REDIS_TOKEN)
_session = requests.Session()


# ─────────────────────────────────────────────
#  SEED ACCOUNT LOGIN
# ─────────────────────────────────────────────

def perform_login(phone: str, password: str) -> dict | None:
    """
    Login a seed account to ClassX, cache token in Redis.
    Returns {"token", "userid", "phone"} or None on failure.
    """
    payload = {
        "source":       (None, "website"),
        "phone":        (None, phone),
        "email":        (None, phone),
        "password":     (None, password),
        "extra_details":(None, "1"),
    }
    try:
        resp = _session.post(
            f"{BASE_URL}/post/userLogin?extra_details=0",
            headers=COMMON_HEADERS,
            files=payload,
            timeout=15
        )
        data = resp.json()
        if resp.status_code == 200 and data.get("status") == 200:
            token  = data["data"]["token"]
            userid = str(data["data"]["userid"])
            redis.set(f"token:{phone}",  token,  ex=TOKEN_TTL)
            redis.set(f"userid:{phone}", userid)
            return {"token": token, "userid": userid, "phone": phone}
    except Exception as e:
        print(f"[AUTH] Login failed for {phone}: {e}")
    return None


# ─────────────────────────────────────────────
#  DYNAMIC ACCOUNTS  (stored by bot)
# ─────────────────────────────────────────────

def get_all_dynamic_accounts() -> list[dict]:
    """Redis se saare dynaccount:* accounts nikalo."""
    try:
        keys = redis.keys("dynaccount:*")
        out = []
        for k in (keys or []):
            val = redis.get(k)
            if val:
                try:
                    out.append(json.loads(val))
                except Exception:
                    pass
        return out
    except Exception:
        return []


def save_dynamic_account(acc: dict) -> None:
    """Bot se call hota hai – dynamic account Redis mein save karo."""
    from config import DYN_ACC_TTL
    key = f"dynaccount:{acc['userid']}"
    redis.set(key, json.dumps(acc), ex=DYN_ACC_TTL)
    print(f"[AUTH] Dynamic account saved: UID={acc['userid']} name={acc.get('name','?')}")


def delete_dynamic_account(userid: str) -> bool:
    key = f"dynaccount:{userid}"
    return bool(redis.delete(key))


# ─────────────────────────────────────────────
#  GET VALID AUTH  (for API calls)
# ─────────────────────────────────────────────

def get_valid_auth() -> dict | None:
    """
    Priority:
      1. Dynamic accounts (freshest tokens)
      2. Seed accounts from Redis cache
      3. Force-relogin seed[0]
    """
    # 1) Dynamic
    dyn = get_all_dynamic_accounts()
    if dyn:
        random.shuffle(dyn)
        for acc in dyn:
            if acc.get("token") and acc.get("userid"):
                return {"token": acc["token"], "userid": str(acc["userid"])}

    # 2) Seed cached
    shuffled = SEED_ACCOUNTS[:]
    random.shuffle(shuffled)
    for acc in shuffled:
        token  = redis.get(f"token:{acc['phone']}")
        userid = redis.get(f"userid:{acc['phone']}")
        if token and userid:
            return {"token": str(token), "userid": str(userid)}

    # 3) Force re-login
    for acc in SEED_ACCOUNTS:
        fresh = perform_login(acc["phone"], acc["pass"])
        if fresh:
            return {"token": fresh["token"], "userid": fresh["userid"]}

    return None


def get_or_login_seed(acc: dict) -> dict | None:
    """Ek specific seed account ka auth lo, refresh karo agar token nahi hai."""
    token  = redis.get(f"token:{acc['phone']}")
    userid = redis.get(f"userid:{acc['phone']}")
    if not token or not userid:
        fresh = perform_login(acc["phone"], acc["pass"])
        if fresh:
            return {"token": fresh["token"], "userid": fresh["userid"]}
        return None
    return {"token": str(token), "userid": str(userid)}
