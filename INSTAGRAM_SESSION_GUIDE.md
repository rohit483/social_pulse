# Instagram Session Management Guide

## Overview

This guide explains how to securely generate Instagram sessions locally and deploy them to production servers (Render, AWS, etc.) without exposing credentials or dealing with IP blocking.

## The Problem

Instagram's security systems:
- ❌ Block automated logins from server IPs immediately
- ❌ Require 2FA/checkpoint verification on unfamiliar IPs
- ❌ Don't allow username/password login on headless servers
- ❌ Block API access from data centers (AWS, Heroku, Render, etc.)

## The Solution: Local Auth & Transfer

**Generate sessions locally** (where Instagram trusts you), then **reuse those sessions on servers**. We have built the system to act completely statelessly.

```
┌──────────────────────────────┐
│  Your Browser (SAFE)         │
│  - Login to Instagram        │
│  - Export Cookies (JSON)     │
└──────────────┬───────────────┘
               │
               ↓
┌──────────────────────────────┐
│  `insta_session` Repository  │
│  - Parses cookies            │
│  - Tests login               │
│  - Exports to Base64 keys    │
└──────────────┬───────────────┘
               │
               ↓
┌──────────────────────────────┐
│  `social_pulse` (This App)   │
│  - Add B64 to .env           │
│  - Instantly load & scrape   │
│  - ZERO direct logins!       │
└──────────────────────────────┘
```

---

## Step 1: Generate Base64 Session Keys

You must use our dedicated helper repository to securely extract sessions from your local browser cookies. 

1. Go to your local instance of the `insta_session` repository.
2. Export your Instagram cookies using a Chrome extension (like "Get cookies.txt LOCALLY") and save them as `cookies.json`.
3. Run the extraction script:
   ```bash
   python extract_sessions.py
   ```
4. The script will securely parse your browser cookies, authenticate with `instaloader` and `instagrapi`, and spit out two extremely long Base64 strings:
   - `INSTAGRAPI_SESSION_B64`
   - `INSTALOADER_SESSION_B64`

---

## Step 2: Local Deployment (Docker)

To run the application locally without IP bans:

1. Open your `.env` file in the root of the `social_pulse` project.
2. Paste the two Base64 strings you just generated:
   ```env
   INSTAGRAPI_SESSION_B64=ew0KICAgICJ1dW...
   INSTALOADER_SESSION_B64=gASV8AEAAAAA...
   ```
3. Boot the system:
   ```bash
   docker-compose up -d --build
   ```
4. The application will instantly load the sessions directly from the environment variables into memory. **It will never attempt to physically log in.**

---

## Step 3: Production Deployment (Render / AWS)

When deploying to a cloud server, the process is identical.

### 1. Go to your Cloud Dashboard (e.g., Render)

Navigate to your project's **Environment Variables** settings.

### 2. Add Environment Variables

Click **"Add Environment Variable"** and set both keys:

| Key | Value |
|-----|-------|
| `INSTAGRAPI_SESSION_B64` | (paste the base64 string) |
| `INSTALOADER_SESSION_B64`| (paste the base64 string) |

*Note: You do NOT need to set `INSTAGRAM_PASSWORD` or any file paths. The system relies entirely on the B64 keys.*

### 3. Deploy

Deploy your application. The app will boot up, detect the environment variables, decode the sessions in memory, and immediately begin scraping without tripping Instagram's server IP detectors!

---

## 💡 Troubleshooting

- **Scraping randomly stopped working? (401 Unauthorized)**
  Your session likely expired or was invalidated by Instagram. Simply log back into Instagram on your computer, export a fresh `cookies.json`, run `extract_sessions.py` again, and update your `.env` variables!
- **Rate Limited? (429 Too Many Requests)**
  Wait 15-30 minutes. The scraper will automatically fail-fast on 429s to prevent hard lockups, and will naturally retry when you initiate another scrape.
