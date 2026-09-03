# 🚀 Sachin Academy Advanced API v3.0

> **Developer:** Maxx Papa  
> Full-featured FastAPI wrapper for ClassX/Sachin Academy with auto-login pool, AES decryption, test series, and Telegram bot sync.

---

## 📁 File Structure

```
sachin_api_v3/
├── main.py          ← FastAPI app (all endpoints)
├── bot.py           ← Telegram log bot (auto account add)
├── auth.py          ← Account pool management
├── crypto.py        ← AES decrypt (from appex_v5.py)
├── notifier.py      ← Telegram HTTP sender
├── config.py        ← All config + env vars
├── requirements.txt
├── .env.example     ← Copy to .env and fill
├── Procfile         ← Railway/Render deploy
└── start.sh         ← Local: API + Bot dono ek saath
```

---

## ⚡ Quick Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. .env banao
cp .env.example .env
# .env mein apni values bharo (BOT_TOKEN, LOG_CHANNEL_ID, API_ID, API_HASH)

# 3. Chalao (API + Bot dono)
bash start.sh

# Ya alag alag:
uvicorn main:app --reload       # API only
python bot.py                   # Bot only
```

---

## 🔑 Environment Variables

| Variable | Description |
|---|---|
| `REDIS_URL` | Upstash Redis URL |
| `REDIS_TOKEN` | Upstash Redis token |
| `BOT_TOKEN` | Telegram bot token (BotFather) |
| `LOG_CHANNEL_ID` | TG channel ID e.g. `-1001234567890` |
| `API_ID` | Pyrogram API ID (my.telegram.org) |
| `API_HASH` | Pyrogram API Hash |
| `ADMIN_IDS` | Comma-separated admin user IDs |

---

## 🌐 API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/user-login` | Public user login → TG log → bot auto-adds |
| `POST` | `/api/login` | Seed account refresh |
| `GET` | `/api/pool-status` | Account pool overview |

### Courses
| Method | Endpoint | Params |
|---|---|---|
| `GET` | `/api/my-batches` | — (all accounts merged) |
| `GET` | `/api/subjects` | `courseid` |
| `GET` | `/api/topics` | `courseid`, `subjectid` |
| `GET` | `/api/videos` | `courseid`, `subjectid`, `topicid` |
| `GET` | `/api/video-details` | `courseid`, `videoid`, `decrypt=true` |
| `GET` | `/api/live-classes` | `courseid`, `start=-1` |
| `GET` | `/api/course-details` | `id` |

### Test Series
| Method | Endpoint | Params |
|---|---|---|
| `GET` | `/api/test-series` | `courseid` |
| `GET` | `/api/test-subjects` | `testseries_id` |
| `GET` | `/api/test-titles` | `testseriesid`, `subject_id`, `search`, `start` |
| `GET` | `/api/test-terms` | `test_id`, `test_series_id`, `test_pass_url` |

### Advanced
| Method | Endpoint | Params |
|---|---|---|
| `GET` | `/api/folder-contents` | `courseid` (full recursive AES-decrypted video list) |

---

## 🤖 Auto-Login Pool Flow

```
User → POST /api/user-login
         ↓
  ClassX API se login
         ↓
  Token Redis mein cache
         ↓
  Full JSON → Telegram log channel
         ↓
  Bot channel monitor kar raha hai
         ↓
  Bot JSON parse karta hai
         ↓
  dynaccount:{userid} Redis mein save
         ↓
  /api/my-batches ab is user ke batches bhi dikhata hai ✅
```

---

## 🛡️ Bot Commands (Admin DM mein)

| Command | Description |
|---|---|
| `/pool` | Saare dynamic accounts dekho |
| `/remove <userid>` | Kisi ek account ko remove karo |
| `/clear_pool` | Saare dynamic accounts delete karo |
| `/status` | Redis + bot status |

---

## 🚢 Deploy on Railway

1. Repo push karo
2. Railway mein `web` + `worker` services banao (Procfile se auto-detect)
3. Environment variables set karo
4. Done ✅

---

## 🔐 Login JSON Example

```json
POST /api/user-login
{
  "identifier": "7361881432",
  "password": "yourpassword"
}
```

Response:
```json
{
  "status": 200,
  "message": "Login successful",
  "data": {
    "userid": "481163",
    "token": "eyJ0eXAiOiJKV1Qi...",
    "name": "jai",
    "email": "jaipk9576@gmail.com",
    "phone": "7361881432"
  }
}
```

---

## 📝 Notes

- `decrypt=true` parameter video-details endpoint mein AES decrypt karta hai automatically
- `/api/test-terms` Next.js buildId auto-detect karta hai (1hr cache, auto-refresh on 404)
- `/api/folder-contents` appex_v5.py ka full recursive extractor hai API form mein
- Dynamic accounts 7 days baad Redis se expire hote hain

---

*Built with ❤️ by Maxx Papa*


## New Features V2
- Auto Batch Add API
- Direct Token Login
- Automatic UserID Extraction from JWT
