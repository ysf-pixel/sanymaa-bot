# 📱 Instagram ↔ Character.AI Bridge Bot

Messages you send to this Instagram account get forwarded to your C.AI character.
Her replies (only the "quoted speech") come back as separate Instagram DMs.

---

## 🗂 Files
```
bot.py            <- the bot itself
requirements.txt  <- Python dependencies
README.md         <- this file
```

---

## 📱 Instagram Setup — You Need 2 Accounts

| Account | Purpose |
|---------|---------|
| **Your real account** | You DM the bot account from here |
| **New bot account** | The bot logs into this one and acts as the bridge |

Create a fresh Instagram account (can be private, fake name is fine).
The bot logs into that account. You DM it from your real account.
Replies from your character come back to your real DMs.

---

## 🔑 Step 1 — Get your tokens

### C.AI Token
1. Open **character.ai** in Chrome
2. Press **F12** → go to **Application** tab → **Cookies** → `https://character.ai`
3. Find the cookie named `HTTP_AUTHORIZATION` — copy its value
   (it starts with `Token abcd1234...`)
4. That's your `CAI_TOKEN`

### Character ID
1. Go to your character's chat page on c.ai
2. Look at the URL: `https://character.ai/chat/XXXXXXXXXXXXXXXX`
3. The part after `/chat/` is your `CHARACTER_ID`

### Your Existing Chat ID (IMPORTANT for memory!)
This makes the bot resume YOUR real conversation so she remembers everything.

1. Open your character chat on c.ai in Chrome
2. Press **F12** → go to **Network** tab
3. Type something in the chat (any message)
4. In the Network tab, look for a request called **`generate`** or **`chat`**
5. Click it → look in the request body or response for `"chat_id"`
6. Copy that UUID (looks like: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
7. That's your `CAI_CHAT_ID`

> If you skip this, the bot starts a brand new chat and she won't remember anything.
> The bot will print the new chat_id in logs — you can grab it and add it later.

### Instagram bot account credentials
Username and password of the **new bot account** you created.

---

## 🚀 Step 2 — Deploy FREE on Render.com

1. **Create a free account** at [render.com](https://render.com)
2. Click **"New +"** → **"Background Worker"**
3. Connect your GitHub repo (or upload the files)
4. Set:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
5. Go to **Environment Variables** and add:

   | Key | Value |
   |-----|-------|
   | `IG_USERNAME` | bot Instagram account username |
   | `IG_PASSWORD` | bot Instagram account password |
   | `CAI_TOKEN` | your C.AI token (from Step 1) |
   | `CHARACTER_ID` | your character's ID (from Step 1) |
   | `CAI_CHAT_ID` | your existing chat ID (from Step 1) — keeps her memory! |

6. Click **Deploy** — it runs 24/7 for free ✓

---

## 🔄 How it works

```
You → DM on Instagram
         ↓
      Bot picks it up (checks every 15 seconds)
         ↓
      Sends your message to C.AI character
         ↓
      C.AI replies (with *actions* and "speech")
         ↓
      Bot strips all *action* text
         ↓
      Each "quoted line" → separate Instagram DM back to you
```

### Example:
C.AI response:
> *She blinks, then snorts in disbelief.*
> "2 PM? Seriously?"
> *She shakes her head, fond annoyance showing.*
> "Idiot… your timing is always off."

What you receive (2 separate DMs):
> `2 PM? Seriously?`
> `Idiot… your timing is always off.`

---

## ⚠️ Important Notes

- **Instagram**: This uses the private mobile API (via `instagrapi`). Don't use your main account — create a secondary one to be safe.
- **C.AI**: Uses an unofficial wrapper. Works until C.AI changes their backend (usually fixed quickly by the library author).
- Both are free tools — $0 cost.
- Render's free tier may spin down after inactivity — upgrade to paid ($7/mo) for always-on reliability.

---

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| IG login fails | Enable "Less secure app access" or use session cookies |
| C.AI token expired | Re-grab it from browser cookies |
| No DMs detected | Make sure someone else is DMing you (bot ignores your own messages) |
| Bot stopped | Re-deploy on Render, check logs |
