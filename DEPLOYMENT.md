# 🎌 Anime Auto Post Bot — Complete Deployment Guide

---

## Table of Contents
1. [Project Structure](#1-project-structure)
2. [Prerequisites](#2-prerequisites)
3. [MongoDB Atlas Setup](#3-mongodb-atlas-setup)
4. [Telegram Bot Setup](#4-telegram-bot-setup)
5. [Local Development](#5-local-development)
6. [GitHub Setup](#6-github-setup)
7. [Render Deployment](#7-render-deployment)
8. [Environment Variables Reference](#8-environment-variables-reference)
9. [Bot Commands & Usage](#9-bot-commands--usage)
10. [Architecture Notes](#10-architecture-notes)

---

## 1. Project Structure

```
anime-bot/
├── main.py                    # FastAPI app + webhook entry point
├── config.py                  # Env-var config dataclass
├── requirements.txt
├── runtime.txt                # Python 3.11
├── Procfile                   # Render start command
├── render.yaml                # Render blueprint (optional)
├── .env.example               # Local env template
├── .gitignore
└── bot/
    ├── core.py                # Pyrogram client + handler registration
    ├── __init__.py
    ├── handlers/
    │   ├── start.py           # /start + deep-link dispatch
    │   ├── post.py            # /post FSM conversation
    │   ├── settings.py        # /setmainchannel, /settemplate
    │   ├── callbacks.py       # Inline button callbacks
    │   └── errors.py          # Error handler stub
    ├── services/
    │   ├── anilist.py         # AniList GraphQL API
    │   └── post_builder.py    # Template render + channel post
    ├── database/
    │   ├── mongo.py           # Motor client wrapper
    │   └── crud.py            # All DB operations
    ├── utils/
    │   ├── fsm.py             # In-memory FSM for conversations
    │   ├── html.py            # HTML escape + formatting helpers
    │   └── admin.py           # Admin guard
    ├── middlewares/
    └── templates/
```

---

## 2. Prerequisites

- Python 3.11+
- A [Telegram account](https://telegram.org) + phone number
- [MongoDB Atlas](https://cloud.mongodb.com) free account
- [Render](https://render.com) free account
- [GitHub](https://github.com) account
- Git installed locally

---

## 3. MongoDB Atlas Setup

1. Go to [https://cloud.mongodb.com](https://cloud.mongodb.com) and **Sign Up / Log In**
2. Click **Build a Database** → Choose **M0 FREE** tier
3. Select a cloud provider (AWS recommended) and a nearby region
4. Set a **Username** and **Password** (save these!)
5. Under **Network Access** → **Add IP Address** → `0.0.0.0/0` (allow all — required for Render)
6. Under **Database** → click **Connect** → **Drivers** → choose **Python 3.6+**
7. Copy the connection string. It looks like:
   ```
   mongodb+srv://youruser:yourpass@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
8. Replace `<password>` with your actual password in the string.
9. This becomes your `MONGO_URI` environment variable.

> **Why Atlas?** All anime posts, settings, and templates are stored here. Data persists across Render redeployments (Render's disk is ephemeral — MongoDB Atlas is permanent).

---

## 4. Telegram Bot Setup

### 4a. Create the Bot

1. Open Telegram → search `@BotFather`
2. Send `/newbot`
3. Follow prompts: choose a name and a username (must end in `bot`)
4. Copy the **API Token** → this is `BOT_TOKEN`
5. Note your bot's `@username` → this is `BOT_USERNAME` (without the `@`)

### 4b. Get API ID & Hash

1. Go to [https://my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Click **API Development Tools**
4. Fill in the form → submit
5. Copy `App api_id` → `API_ID`
6. Copy `App api_hash` → `API_HASH`

### 4c. Get Your Admin User ID

1. Open Telegram → search `@userinfobot`
2. Send `/start`
3. It replies with your numeric user ID → add to `ADMIN_IDS`
4. For multiple admins: `ADMIN_IDS=123456789,987654321`

### 4d. Prepare the Channel

1. Create (or use existing) a Telegram channel
2. Add your bot as an **Administrator** with **Post Messages** permission
3. Note the channel's numeric ID:
   - Forward a message from the channel to `@userinfobot` OR
   - Use `/setmainchannel` command after deploying

---

## 5. Local Development

```bash
# Clone the repo
git clone https://github.com/yourname/anime-bot.git
cd anime-bot

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up env vars
cp .env.example .env
# Edit .env with your values

# Run locally (polling won't work in webhook mode without a public URL)
# Use ngrok for local webhook testing:
ngrok http 8000
# Then set WEBHOOK_URL=https://xxxx.ngrok-free.app in .env

python main.py
```

---

## 6. GitHub Setup

```bash
cd anime-bot

git init
git add .
git commit -m "Initial commit — Anime Auto Post Bot"

# Create repo on GitHub (https://github.com/new)
git remote add origin https://github.com/YOURNAME/anime-bot.git
git branch -M main
git push -u origin main
```

> **IMPORTANT:** Never commit your `.env` file. It's in `.gitignore`. Always use environment variables on Render.

---

## 7. Render Deployment

### Step 1 — Create Web Service

1. Log in to [https://render.com](https://render.com)
2. Click **New** → **Web Service**
3. Connect your GitHub account and select the `anime-bot` repository
4. Configure:
   - **Name:** `anime-bot` (or any name)
   - **Region:** Oregon (US West) or closest to you
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** `Free`
5. Click **Create Web Service**
6. Wait for first deploy to complete. You'll get a URL like:
   ```
   https://anime-bot-xxxx.onrender.com
   ```

### Step 2 — Set Environment Variables

In Render dashboard → your service → **Environment** tab, add:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | Your BotFather token |
| `BOT_USERNAME` | Your bot's username (no @) |
| `API_ID` | From my.telegram.org |
| `API_HASH` | From my.telegram.org |
| `ADMIN_IDS` | Comma-separated user IDs |
| `MONGO_URI` | Your Atlas connection string |
| `DB_NAME` | `animebot` |
| `WEBHOOK_URL` | `https://anime-bot-xxxx.onrender.com` |

> **Note:** `PORT` is auto-injected by Render (value `10000`). Do not set it manually.

### Step 3 — Redeploy

After setting env vars:
- Go to **Deploys** tab → click **Deploy latest commit**
- Wait for deploy to complete
- Check logs — you should see:
  ```
  ✅ MongoDB connected.
  ✅ Webhook set → https://anime-bot-xxxx.onrender.com/webhook/YOUR_TOKEN
  ✅ All handlers registered.
  ```

### Step 4 — Keep-Alive (Free Tier)

Render free tier spins down after 15 minutes of inactivity. Use a free uptime monitor:

- [UptimeRobot](https://uptimerobot.com) (free)
- Add your `/health` endpoint: `https://anime-bot-xxxx.onrender.com/health`
- Set check interval: **5 minutes**

This prevents cold starts and ensures the webhook is always responsive.

---

## 8. Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | ✅ | Telegram bot token from BotFather |
| `BOT_USERNAME` | ✅ | Bot's @username without the @ |
| `API_ID` | ✅ | Telegram API ID from my.telegram.org |
| `API_HASH` | ✅ | Telegram API hash from my.telegram.org |
| `ADMIN_IDS` | ✅ | Comma-separated admin user IDs |
| `MONGO_URI` | ✅ | MongoDB Atlas connection string |
| `DB_NAME` | ❌ | Database name (default: `animebot`) |
| `WEBHOOK_URL` | ✅ | Your Render service public URL |
| `PORT` | ❌ | Server port (auto-set by Render to 10000) |

---

## 9. Bot Commands & Usage

### Admin Commands

| Command | Description |
|---------|-------------|
| `/start` | Bot welcome message |
| `/settings` | View current bot settings |
| `/setmainchannel` | Set the channel to post to |
| `/post <anime> <episode>` | Start anime post creation |
| `/skip` | Skip current quality input |
| `/cancel` | Cancel current operation |
| `/settemplate channel_post` | Edit the channel post template |
| `/settemplate bot_message` | Edit the bot quality-selection template |
| `/gettemplate <name>` | View a template |

### Full Post Workflow

```
1. Admin: /post Dandadan Episode 08

2. Bot fetches from AniList:
   ✅ Found: Dandadan
   Episode: 08 | Season: FALL | Rating: 84/100

3. Bot: "Send 480p link (or /skip)"
   Admin: https://t.me/filebot?start=abc480

4. Bot: "Send 720p link (or /skip)"
   Admin: https://t.me/filebot?start=abc720

5. Bot: "Send 1080p link (or /skip)"
   Admin: /skip

6. Bot: "Send 4K link (or /skip)"
   Admin: /skip

7. Bot shows preview with [✅ Post Now] [❌ Cancel] buttons

8. Admin clicks ✅ Post Now

9. Bot posts to channel with cover image + formatted text + [DOWNLOAD] button

10. User clicks [DOWNLOAD] in channel
    → Opens bot with deep-link: t.me/YourBot?start=xK3mP9aQwZ

11. Bot shows quality buttons:
    [📥 480P]  [📥 720P]

12. User clicks quality → redirected to external file bot
```

### Template Variables

| Variable | Description |
|----------|-------------|
| `{title}` | Romaji title |
| `{english_title}` | English title |
| `{episode}` | Episode number/label |
| `{season}` | Season (FALL, WINTER, etc.) |
| `{qualities}` | Quality list |
| `{download_link}` | Deep-link URL |

---

## 10. Architecture Notes

### Why Webhook (not polling)?
- Render free tier has no persistent background process
- Webhook receives updates only when needed = zero idle CPU
- Polling requires a running loop — wastes Render's free compute

### Why In-Memory FSM?
- Conversation states are transient (seconds to minutes)
- MongoDB writes for every step would be unnecessary overhead
- If the server restarts mid-conversation, admin can simply `/cancel` and restart

### Why MongoDB Atlas?
- Render's free tier has **ephemeral disk** — local SQLite is wiped on redeploy
- Atlas free tier (M0) = 512MB storage, plenty for metadata
- Motor (async driver) = non-blocking, perfect for async FastAPI

### Data Persistence Guarantee
All permanent data (anime posts, settings, templates) is stored in MongoDB Atlas:
- Redeployments on Render do NOT delete your data
- Only in-memory FSM sessions are lost on restart (which is expected)

### Render Free Tier Limits
- 750 hours/month (enough for 1 service running 24/7)
- Spins down after 15 min inactivity → use UptimeRobot pings
- 512MB RAM → this bot uses ~80-120MB normally
- Shared CPU → async architecture handles this well
