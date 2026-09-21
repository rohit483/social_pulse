# Social Pulse 🚀

**Social Pulse** is a smart tool for scraping and analyzing Instagram comments using Instagrapi and a Gen-Z aware Sentiment Engine.

Whether you're a data enthusiast, a marketer, or just curious, Social Pulse makes it easy to grab comments and visualize the vibe.

---

## ✨ Features

### 📸 Instagram Comment Scraper

- **Instagrapi-only provider**: Uses the configured Instagrapi session to request up to 200 comments.
- **Session management**: Refresh `cookie.json` and regenerate `INSTAGRAPI_SESSION_B64` when Instagram invalidates the session.
- **Lazy Loading**: Scraper resources are only initialized when the scrape button is clicked, ensuring instant app startup.

### 🧠 Advanced Sentiment Analysis

- **VADER-Powered**: Uses `vaderSentiment` for superior accuracy with social media text.
- **Custom Slang Lexicon**: Patched engine understands Gen-Z slang (e.g., `fire`, `lit`, `based`, `w`, `no cap`) and emojis that standard libraries often miss.
- **Data Integrity**: Full UTF-8 support ensures emojis and special characters are preserved.
- **📂 Data Export**: Download your data as raw CSVs or fully analyzed reports.

---

## 📂 Project Structure

```text
social_pulse/
├── app.py                  # Main Flask Application
├── Dockerfile              # Docker Image Config
├── docker-compose.yml      # Service Orchestration
├── extract_sessions.py     # Automated Cookie Parser
├── requirements.txt        # Project Dependencies
├── nginx.conf              # Nginx Reverse Proxy Config
├── modules/                # Core Logic Modules
│   ├── database/           # PostgreSQL DB Models
│   ├── analysis/           # Sentiment Analysis Engine
│   ├── configuration/      # Config & Env Management
│   └── instagram/          # Scraper & Login Logic
├── static/                 # CSS, JS & Assets
├── templates/              # HTML Templates
├── cookie.json             # Your Instagram cookies (gitignored)
└── troubleshooting.md      # Solutions to common errors
```

---

## 🐳 Quick Start (Docker)

To protect your IP and make deployment seamless, Social Pulse is designed to run in Docker and automatically extract sessions from your local browser cookies.

### 1. Export Cookies from Chrome (Authentication)

Instagram blocks automated logins from servers. To get around this, we **extract sessions locally** where Instagram trusts your IP address.

1. Install the **[EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg)** or **[J2Team Cookies](https://chrome.google.com/webstore/detail/j2team-cookies/jjpjijpjndedcempgkndkhaenkeeniha)** Chrome extension.
2. Go to [instagram.com](https://www.instagram.com/) and log into a **burner account**.
3. Open the extension and click the **"Export"** button (which copies the cookies to your clipboard in JSON format).
4. Open a text editor, paste the contents, and save the file exactly as `cookie.json` in the root folder of this project.

### 2. Boot the Application

```bash
# Boot the database, proxy, and backend
docker-compose up
```

**That's it!** 
When the container starts, it detects `cookie.json`, extracts the Instagrapi session, and starts the app.

Open `http://localhost` (or Port 80) in your browser.

---

## 💡 Troubleshooting

Having issues with `cookie.json`, database connections, or UI glitches?
👉 **Please check out the [`troubleshooting.md`](https://github.com/rohit483/social_pulse/blob/main/troubleshooting.md) for quick fixes!**

---

## 🤝 Contribution

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 🔮 Future Roadmap

- [x] **Database Integration**: Migrated from CSV to PostgreSQL!
- [ ] **Multi-Platform Support**: Architecture ready for Facebook & Twitter modules.
- [ ] **Visual Dashboards**: Add chart.js visualizations for sentiment trends.

---

## 📜 License

Distributed under the AGPLv3 License. See [`LICENSE`](https://github.com/rohit483/social_pulse/blob/main/LICENSE) for more information.
