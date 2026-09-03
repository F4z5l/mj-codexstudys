import os

# ========== REDIS ==========
REDIS_URL   = os.getenv("REDIS_URL",   "https://winning-lioness-97755.upstash.io")
REDIS_TOKEN = os.getenv("REDIS_TOKEN", "gQAAAAAAAX3bAAIgcDExMDY4NGY2OWZlZGY0OWY0ODA0NmNmZDNlM2JhNGUxOA")

# ========== TELEGRAM ==========
BOT_TOKEN      = os.getenv("BOT_TOKEN", "")          # e.g. 123456:ABC-xyz
API_ID         = int(os.getenv("API_ID", "0"))        # from my.telegram.org
API_HASH       = os.getenv("API_HASH", "")            # from my.telegram.org
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))  # e.g. -1001234567890
ADMIN_IDS      = list(map(int, os.getenv("ADMIN_IDS", "0").split(",")))

# ========== CLASSX ==========
BASE_URL  = "https://sachinacademyapi.classx.co.in"
NEXT_BASE = "https://sachinacademy.classx.co.in"

COMMON_HEADERS = {
    "Auth-Key":       "appxapi",
    "Client-Service": "Appx",
    "Source":         "website",
    "User-Agent":     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/146.0.0.0 Safari/537.36",
    "Origin":         "https://sachinacademy.classx.co.in",
    "Referer":        "https://sachinacademy.classx.co.in/"
}

# Seed accounts (always-present pool)
SEED_ACCOUNTS = [
    {"phone": "9140256954", "pass": "Vikas@9651"},
    {"phone": "9508063031", "pass": "Soni@95080"},
]

# AES keys (ClassX standard)
AES_KEY = b'638udh3829162018'
AES_IV  = b'fedcba9876543210'

# Redis TTLs
TOKEN_TTL   = 86400        # 1 day
DYN_ACC_TTL = 86400 * 7   # 7 days
BUILD_ID_TTL = 3600        # 1 hour
