import asyncio
import re
import os
import json
import logging
from instagrapi import Client as IGClient
from PyCharacterAI import get_client as get_cai_client

# ─────────────────────────────────────────────
#  CONFIG — set these as environment variables on Render
# ─────────────────────────────────────────────

# Instagram BOT account (new separate account, not your real one)
IG_USERNAME  = os.getenv("IG_USERNAME", "your_bot_ig_username")
IG_PASSWORD  = os.getenv("IG_PASSWORD", "your_bot_ig_password")

# Character.AI — all found!
CAI_TOKEN    = os.getenv("CAI_TOKEN",    "Token 6d017ef96f9ee84e57845ef5b922301199d8f9b0")
CHARACTER_ID = os.getenv("CHARACTER_ID", "R7ICd5_RcveDEVdU3oEgTc3djpJQoG1omr1-UN38Oes")
CAI_CHAT_ID  = os.getenv("CAI_CHAT_ID",  "bd840c37-c2a1-4d91-b307-ae9ff49bcbea")

# How often to check Instagram DMs (seconds)
POLL_INTERVAL   = 15
IG_SESSION_FILE = "ig_session.json"

# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s"
)
log = logging.getLogger(__name__)


def extract_quotes(text: str) -> list[str]:
    """
    Extract only spoken dialogue from C.AI response.
    Strips all *action* text, keeps only "quoted speech".
    Each quote becomes a separate Instagram DM.

    Example:
      *She blinks.*  "2 PM? Seriously?"  *She shakes her head.*  "Idiot."
    Returns: ["2 PM? Seriously?", "Idiot."]
    """
    quotes = re.findall(r'[\u201c"](.+?)[\u201d"]', text, re.DOTALL)
    cleaned = [q.strip().replace("\n", " ") for q in quotes if q.strip()]
    return cleaned


class Bot:
    def __init__(self):
        self.ig  = IGClient()
        self.cai = None
        self.last_seen: dict[str, str] = self._load_state()

    def _load_state(self) -> dict:
        if os.path.exists("bot_state.json"):
            with open("bot_state.json") as f:
                return json.load(f)
        return {}

    def _save_state(self):
        with open("bot_state.json", "w") as f:
            json.dump(self.last_seen, f)

    # ── Instagram login ────────────────────────────────────────────────────
    def ig_login(self):
        if os.path.exists(IG_SESSION_FILE):
            log.info("Loading saved IG session...")
            self.ig.load_settings(IG_SESSION_FILE)
            self.ig.login(IG_USERNAME, IG_PASSWORD)
        else:
            log.info("Fresh IG login...")
            self.ig.login(IG_USERNAME, IG_PASSWORD)
            self.ig.dump_settings(IG_SESSION_FILE)
        log.info("Instagram: logged in OK")

    # ── C.AI login with token ──────────────────────────────────────────────
    async def cai_login(self):
        log.info("Connecting to Character.AI...")
        self.cai = await get_cai_client(token=CAI_TOKEN)
        me = await self.cai.account.fetch_me()
        log.info(f"Character.AI: logged in as @{me.username}")
        log.info(f"Resuming chat with Sanymaa: {CAI_CHAT_ID}")

    # ── Send message to C.AI, return only quoted speech ───────────────────
    async def ask_character(self, user_message: str) -> list[str]:
        answer = await self.cai.chat.send_message(
            CHARACTER_ID,
            CAI_CHAT_ID,
            user_message
        )
        raw = answer.get_primary_candidate().text
        log.info(f"C.AI raw: {raw[:120]}...")
        quotes = extract_quotes(raw)
        if not quotes:
            # Fallback: no quotes found, send full reply
            quotes = [raw.strip()]
        return quotes

    # ── Poll Instagram DMs ─────────────────────────────────────────────────
    async def poll_instagram(self):
        log.info("Checking Instagram DMs...")
        try:
            threads = self.ig.direct_threads(amount=10)
        except Exception as e:
            log.error(f"Failed to fetch IG threads: {e}")
            return

        for thread in threads:
            thread_id    = str(thread.id)
            messages     = thread.messages
            if not messages:
                continue

            last_id      = self.last_seen.get(thread_id)
            new_messages = []

            for msg in reversed(messages):  # oldest first
                msg_id = str(msg.id)
                if last_id is None or msg_id > last_id:
                    new_messages.append(msg)

            for msg in new_messages:
                if msg.item_type != "text":
                    continue
                if str(msg.user_id) == str(self.ig.user_id):
                    continue  # skip our own replies

                user_text = msg.text
                log.info(f"[IG -> CAI] {user_text!r}")

                try:
                    reply_lines = await self.ask_character(user_text)
                except Exception as e:
                    log.error(f"C.AI error: {e}")
                    continue

                # Send each quoted line as a separate DM
                for line in reply_lines:
                    log.info(f"[CAI -> IG] {line!r}")
                    try:
                        self.ig.direct_send(line, thread_ids=[thread.id])
                        await asyncio.sleep(1.2)
                    except Exception as e:
                        log.error(f"Failed to send IG message: {e}")

                self.last_seen[thread_id] = str(msg.id)

        self._save_state()

    # ── Main loop ──────────────────────────────────────────────────────────
    async def run(self):
        self.ig_login()
        await self.cai_login()
        log.info(f"Bot running — polling every {POLL_INTERVAL}s")
        while True:
            await self.poll_instagram()
            await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    bot = Bot()
    asyncio.run(bot.run())
