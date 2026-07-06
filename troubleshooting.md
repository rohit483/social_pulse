# 💡 Troubleshooting Guide

This guide covers the most common issues you might face when deploying or running Social Pulse, and how to fix them quickly!

---

## 1. Authentication & Session Errors

### 🔴 Error: `[!] cookie.json is empty. Skipping session extraction.`
**Why it happens:** Docker started up, but your `cookie.json` file is empty (e.g., just `[]`) or missing valid cookies.
**How to fix:**
1. Open Google Chrome and log into your **burner Instagram account**.
2. Click your cookie export extension (like *EditThisCookie* or *J2Team Cookies*).
3. Click **Export** to copy the JSON.
4. Paste it into `cookie.json` in the root folder of this project.
5. Restart your docker containers: `docker-compose restart social-pulse`

### 🔴 Error: `Login Required` or `Something went wrong` during scraping
**Why it happens:** Your Instagram session has expired, or Instagram has flagged your burner account and forced a password reset.
**How to fix:**
1. Open your browser and go to Instagram.com.
2. If it asks you to confirm your identity or change your password, do it.
3. Once you can view feeds normally again, re-export your cookies to `cookie.json`.
4. Restart your docker container to extract the fresh sessions.

---

## 2. Database Errors

### 🔴 Error: `Failed to save scrape to DB` or `psycopg2.OperationalError`
**Why it happens:** The Flask backend cannot talk to the PostgreSQL database container.
**How to fix:**
1. Ensure you are using `docker-compose up` so both the database and web app start together.
2. Check your `.env` file (if you have one) to ensure you haven't overwritten the standard Postgres credentials.
3. If the database volume got corrupted, you can factory reset it (Warning: deletes all scraped data):
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

---

## 3. General App Issues

### 🔴 Error: `Port 5000 (or 80) is already in use`
**Why it happens:** You have another application or a ghost Docker container running on the same port.
**How to fix:**
1. Shut down existing containers: `docker-compose down`
2. If it's a local app, find what is using the port and close it, or change the port mapping in `docker-compose.yml` (e.g., `"8080:5000"`).

### 🔴 Error: UI looks broken or CSS isn't loading
**Why it happens:** Your browser has heavily cached an old version of `style.css` or `script.js`.
**How to fix:**
Perform a "Hard Refresh" in your browser:
- **Windows/Linux:** `Ctrl + F5` or `Ctrl + Shift + R`
- **Mac:** `Cmd + Shift + R`

### 🔴 Issue: File downloads have generic names (e.g., `download.csv`)
**Why it happens:** You are using an outdated version of the code. We recently updated the app to use highly descriptive filenames like `Raw_Instagram_Comments_abc123.csv`.
**How to fix:**
1. Pull the latest code from GitHub.
2. Rebuild the docker container to bake in the new Javascript:
   ```bash
   docker-compose up --build -d
   ```
