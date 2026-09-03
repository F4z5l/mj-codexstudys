"""
bot.py  –  Sachin Academy Log Bot  v5  (Channel-as-Database)
═════════════════════════════════════════════════════════════

🔑 Main Feature — Startup Channel Sync:
   Bot jab bhi start/restart/redeploy ho:
     1. Channel ki PURI history padhta hai (last 5000 messages)
     2. Har #SYNC_ACCOUNT# message se account data nikalta hai
     3. Redis mein dynaccount:{userid} se save karta hai
     4. Ab /api/my-batches mein saare accounts wapas aa jaate hain

   Result: Channel = Permanent Database
   Render pe jitni baar bhi redeploy karo — koi data lost nahi.

Real-time listener:
   - Naya login aaye → #DATA# line se parse → save

Admin commands (private DM):
   /start  /pool  /remove <userid>  /clear_pool  /status  /sync
"""

import json
import re
import sys
import asyncio

from pyrogram import Client, filters, idle
from pyrogram.types import Message
from upstash_redis import Redis

from config import (
    API_ID, API_HASH, BOT_TOKEN,
    LOG_CHANNEL_ID, ADMIN_IDS,
    REDIS_URL, REDIS_TOKEN
)
from auth import (
    save_dynamic_account,
    get_all_dynamic_accounts,
    delete_dynamic_account
)

# ── Checks ────────────────────────────────────────────────────────────────────
if not BOT_TOKEN:
    print("[BOT] ❌ BOT_TOKEN missing — exiting gracefully.")
    sys.exit(0)
if not API_ID or not API_HASH:
    print("[BOT] ❌ API_ID/API_HASH missing — exiting gracefully.")
    sys.exit(0)
if not LOG_CHANNEL_ID:
    print("[BOT] ❌ LOG_CHANNEL_ID missing — exiting gracefully.")
    sys.exit(0)

# ── Redis + Bot ───────────────────────────────────────────────────────────────
redis = Redis(url=REDIS_URL, token=REDIS_TOKEN)

bot = Client(
    name      = "sachin_log_bot",
    api_id    = API_ID,
    api_hash  = API_HASH,
    bot_token = BOT_TOKEN,
    in_memory = True        # Render ephemeral FS ke liye CRITICAL
)


# ══════════════════════════════════════════════════════════════════════════════
#  PARSERS
# ══════════════════════════════════════════════════════════════════════════════

def _parse_sync_account(text: str) -> dict | None:
    """
    MSG 2 format parse karo:
        #SYNC_ACCOUNT#
        {"userid":...,"token":...,"name":...,"email":...,"phone":...}
    Yeh sabse reliable format hai — startup scan mein yahi use hota hai.
    """
    if "#SYNC_ACCOUNT#" not in text:
        return None
    try:
        # #SYNC_ACCOUNT# ke baad wali line mein JSON hota hai
        lines = text.strip().splitlines()
        for i, line in enumerate(lines):
            if "#SYNC_ACCOUNT#" in line:
                # JSON same line mein ya next line mein ho sakta hai
                json_str = line.replace("#SYNC_ACCOUNT#", "").strip()
                if not json_str and i + 1 < len(lines):
                    json_str = lines[i + 1].strip()
                if json_str:
                    return json.loads(json_str)
    except Exception as e:
        print(f"[BOT] _parse_sync_account error: {e}")
    return None


def _parse_data_line(text: str) -> dict | None:
    """
    MSG 1 format — #DATA# line:
        #DATA# {"userid":...,"token":...}
    Real-time listener yahi use karta hai.
    """
    m = re.search(r'#DATA#\s*(\{.+\})', text)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except Exception as e:
            print(f"[BOT] _parse_data_line error: {e}")
    return None


def _parse_fields_fallback(text: str) -> dict | None:
    """Last resort — regex se fields nikalo."""
    uid   = re.search(r'UserID\s*:\s*(\d+)',              text)
    tok   = re.search(r'Token\s*:\s*([A-Za-z0-9._\-]+)', text)
    name  = re.search(r'Name\s*:\s*(.+)',                 text)
    phone = re.search(r'Phone\s*:\s*(\d+)',               text)
    email = re.search(r'Email\s*:\s*(\S+)',               text)
    if uid and tok:
        return {
            "userid": uid.group(1).strip(),
            "token":  tok.group(1).strip(),
            "name":   name.group(1).strip()  if name  else "Unknown",
            "phone":  phone.group(1).strip() if phone else "",
            "email":  email.group(1).strip() if email else "",
        }
    return None


def _is_valid_acc(acc: dict) -> bool:
    return bool(
        acc
        and acc.get("userid")
        and acc.get("token")
        and str(acc["userid"]).isdigit()
        and len(acc["token"]) > 20
    )


def _is_admin(msg: Message) -> bool:
    return bool(msg.from_user and msg.from_user.id in ADMIN_IDS)


# ══════════════════════════════════════════════════════════════════════════════
#  STARTUP CHANNEL SYNC  ← Main Feature
# ══════════════════════════════════════════════════════════════════════════════

async def startup_sync(client: Client) -> tuple[int, int]:
    """
    Bot start hone par channel ki puri history padhkar
    saare accounts Redis mein restore karo.

    Priority parsing order:
      1. #SYNC_ACCOUNT# message  (sabse reliable)
      2. #DATA# line             (real-time format)
      3. Regex fallback          (purane format ke liye)

    Returns: (restored_count, total_found)
    """
    print(f"[BOT] 🔄 Startup sync shuru — channel {LOG_CHANNEL_ID} history padh raha hun...")

    restored  = 0
    refreshed = 0
    failed    = 0
    seen_uids = set()

    try:
        # Last 5000 messages padho (channel backup ke liye kaafi hai)
        async for message in client.get_chat_history(LOG_CHANNEL_ID, limit=5000):
            text = message.text or message.caption or ""

            # Quick filter — irrelevant messages skip karo
            if (
                "#SYNC_ACCOUNT#" not in text
                and "#DATA#"        not in text
                and "NEW USER LOGIN" not in text
                and "UserID"         not in text
            ):
                continue

            # Parse — 3 methods try karo
            acc = (
                _parse_sync_account(text)
                or _parse_data_line(text)
                or _parse_fields_fallback(text)
            )

            if not _is_valid_acc(acc):
                failed += 1
                continue

            uid = str(acc["userid"])

            # Same UID dobara process mat karo
            # (Channel mein ek user ke multiple messages ho sakte hain —
            #  sabse purana message pehle aata hai history mein, lekin
            #  hum sabse naya chahte hain isliye seen check karo)
            if uid in seen_uids:
                continue
            seen_uids.add(uid)

            # Redis mein already hai?
            existing = redis.get(f"dynaccount:{uid}")
            if existing:
                refreshed += 1
                # Refresh karo (TTL reset)
                save_dynamic_account(acc)
            else:
                save_dynamic_account(acc)
                restored += 1

        total_found = restored + refreshed
        print(
            f"[BOT] ✅ Sync complete!\n"
            f"       New restored : {restored}\n"
            f"       Refreshed    : {refreshed}\n"
            f"       Parse failed : {failed}\n"
            f"       Total pool   : {len(get_all_dynamic_accounts())}"
        )

        # Channel pe sync report bhejo
        try:
            pool_size = len(get_all_dynamic_accounts())
            await client.send_message(
                LOG_CHANNEL_ID,
                f"🤖 <b>Bot Started — Channel Sync Complete</b>\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"✅ New accounts restored : <b>{restored}</b>\n"
                f"🔄 Existing refreshed   : <b>{refreshed}</b>\n"
                f"👥 Total pool size      : <b>{pool_size}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"<i>/api/my-batches ab {pool_size} accounts se batches dikhayega</i>",
                parse_mode="html"
            )
        except Exception as e:
            print(f"[BOT] Sync report send failed: {e}")

        return restored, total_found

    except Exception as e:
        print(f"[BOT] ❌ Startup sync error: {e}")
        return 0, 0


# ══════════════════════════════════════════════════════════════════════════════
#  REAL-TIME CHANNEL LISTENER
# ══════════════════════════════════════════════════════════════════════════════

@bot.on_message(filters.channel & filters.chat(LOG_CHANNEL_ID))
async def on_log_channel_msg(client: Client, message: Message):
    """
    Naye login messages real-time mein process karo.
    #SYNC_ACCOUNT# messages skip karo (woh machine format hai,
    auto-confirm message send nahi karna chahiye uspe).
    """
    text = message.text or message.caption or ""

    # Machine sync messages skip karo
    if "#SYNC_ACCOUNT#" in text:
        return

    # Sirf login messages
    if "NEW USER LOGIN" not in text and "UserID" not in text and "#DATA#" not in text:
        return

    # Parse
    acc = (
        _parse_data_line(text)
        or _parse_fields_fallback(text)
    )

    if not _is_valid_acc(acc):
        print("[BOT] ⚠️ Real-time: Could not parse account data")
        return

    uid = str(acc["userid"])
    print(f"[BOT] 📩 Real-time login detected: uid={uid} name={acc.get('name','?')}")

    # Save (API pehle se save kar chuka hoga, yeh refresh hai)
    save_dynamic_account(acc)

    # Confirmation message
    try:
        await client.send_message(
            LOG_CHANNEL_ID,
            f"✅ <b>Pool updated!</b>\n"
            f"👤 <b>{acc.get('name', 'N/A')}</b>  "
            f"(UID: <code>{uid}</code>)\n"
            f"📱 {acc.get('phone','?')}  |  📧 {acc.get('email','?')}",
            parse_mode="html"
        )
    except Exception as e:
        print(f"[BOT] Confirm send failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@bot.on_message(filters.command("start") & filters.private)
async def cmd_start(client: Client, message: Message):
    await message.reply(
        "👋 <b>Sachin Academy Log Bot v5</b>\n\n"
        "🔧 <b>Commands:</b>\n"
        "  /pool — Dynamic account pool\n"
        "  /sync — Channel se abhi sync karo\n"
        "  /remove &lt;userid&gt; — Account hatao\n"
        "  /clear_pool — Saare dynamic accounts delete\n"
        "  /status — Bot + Redis status\n\n"
        "💡 <i>Bot restart hone par automatically\n"
        "   channel history se saare accounts restore hote hain.</i>",
        parse_mode="html"
    )


@bot.on_message(filters.command("pool") & filters.private)
async def cmd_pool(client: Client, message: Message):
    if not _is_admin(message):
        return await message.reply("❌ Admin only.")
    accs = get_all_dynamic_accounts()
    if not accs:
        return await message.reply("📭 Pool empty hai.")
    lines = [f"👥 <b>Dynamic Pool ({len(accs)} accounts)</b>\n"]
    for i, a in enumerate(accs, 1):
        lines.append(
            f"{i}. <b>{a.get('name','N/A')}</b>  "
            f"UID: <code>{a.get('userid')}</code>\n"
            f"   📱 {a.get('phone','?')}  |  📧 {a.get('email','?')}"
        )
    # TG message limit ke liye split karo
    chunk = ""
    for line in lines:
        if len(chunk) + len(line) > 3800:
            await message.reply(chunk, parse_mode="html")
            chunk = ""
        chunk += line + "\n"
    if chunk:
        await message.reply(chunk, parse_mode="html")


@bot.on_message(filters.command("sync") & filters.private)
async def cmd_sync(client: Client, message: Message):
    """Manual sync trigger — /sync command se karo."""
    if not _is_admin(message):
        return await message.reply("❌ Admin only.")
    await message.reply("🔄 Channel sync shuru kar raha hun... thoda wait karo.")
    restored, total = await startup_sync(client)
    pool = len(get_all_dynamic_accounts())
    await message.reply(
        f"✅ <b>Sync complete!</b>\n"
        f"Restored: <b>{restored}</b>  |  Total pool: <b>{pool}</b>",
        parse_mode="html"
    )


@bot.on_message(filters.command("remove") & filters.private)
async def cmd_remove(client: Client, message: Message):
    if not _is_admin(message):
        return await message.reply("❌ Admin only.")
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("Usage: /remove &lt;userid&gt;", parse_mode="html")
    uid = parts[1].strip()
    ok  = delete_dynamic_account(uid)
    await message.reply(
        f"{'🗑️ Removed' if ok else '⚠️ Not found'}: UID <code>{uid}</code>",
        parse_mode="html"
    )


@bot.on_message(filters.command("clear_pool") & filters.private)
async def cmd_clear_pool(client: Client, message: Message):
    if not _is_admin(message):
        return await message.reply("❌ Admin only.")
    accs = get_all_dynamic_accounts()
    for a in accs:
        delete_dynamic_account(a["userid"])
    await message.reply(f"🗑️ <b>{len(accs)} accounts</b> clear kar diye.", parse_mode="html")


@bot.on_message(filters.command("status") & filters.private)
async def cmd_status(client: Client, message: Message):
    if not _is_admin(message):
        return await message.reply("❌ Admin only.")
    try:
        redis.ping()
        redis_ok = "✅ Online"
    except Exception:
        redis_ok = "❌ Down"
    dyn = len(get_all_dynamic_accounts())
    await message.reply(
        f"📊 <b>Status</b>\n"
        f"🗄️ Redis   : {redis_ok}\n"
        f"👥 Pool    : <b>{dyn}</b> dynamic accounts\n"
        f"📡 Channel : <code>{LOG_CHANNEL_ID}</code>\n"
        f"🔑 Admins  : {ADMIN_IDS}",
        parse_mode="html"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN — Proper async startup with channel sync
# ══════════════════════════════════════════════════════════════════════════════

async def main():
    print("🤖 Sachin Academy Log Bot v5 starting...")
    print(f"   Channel : {LOG_CHANNEL_ID}")
    print(f"   Admins  : {ADMIN_IDS}")
    print(f"   Mode    : in_memory (Render safe)")

    await bot.start()
    print("[BOT] ✅ Connected to Telegram")

    # ── Startup sync — channel history se saare accounts restore karo ──────
    await startup_sync(bot)

    print("[BOT] 🟢 Bot ready — listening for new logins...")
    await idle()       # bot yahan tak run karta rahega
    await bot.stop()
    print("[BOT] Stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
