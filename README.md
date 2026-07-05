# Social Pulse 🚀

**Social Pulse** is a smart tool for scraping and analyzing Instagram comments. It helps you understand what people are really saying by using a **Hybrid Scraper** (Instaloader + Instagrapi) and a **Gen-Z aware Sentiment Engine**.

Whether you're a data enthusiast, a marketer, or just curious, Social Pulse makes it easy to grab comments and visualize the vibe.

---

## ✨ Features

### 📸 Fail-Proof Hybrid Scraper

- **Dual-Engine System**: Combines the strengths of two powerful libraries:
  - **Primary**: `instaloader` (Fast, efficient for standard interaction).
  - **Fallback**: `instagrapi` (Mimics mobile API, highly resistant to bot detection).
- **Auto-Failover**: If the primary engine encounters a "Login Required" or connection error, the system automatically switches to the fallback engine without crashing.
- **Robust Session Management**: Maintains separate session files for each engine to ensure stability.
- **Session Warm-up**: Automatically "warms up" fresh sessions with dummy API calls to prevent "Something went wrong" errors on the first scrape.
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
├── nginx.conf              # Reverse Proxy Config
├── requirements.txt        # Project Dependencies
├── modules/                # Core Logic Modules
│   ├── analysis/           # Sentiment Analysis Engine
│   ├── configuration/      # Config & Env Management
│   └── instagram/          # Scraper & Login Logic
├── static/                 # CSS, JS & Assets
│   ├── style.css
│   └── script.js
├── templates/              # HTML Templates
│   └── index.html
├── webdata/                # Generated Reports & Uploads
│   ├── csv uploads/
│   └── csv downloads/
├── .env                    # Secrets file
└── sp_env/                 # Virtual Environment (gitignored)
```

---

## 🛠️ Quick Start (Local)

Run Social Pulse on your machine in minutes.

### Prerequisites

- Python 3.10 or higher
- An Instagram account (for scraping)

### 1. Setup

```bash
# Clone the repo
git clone https://github.com/rohit483/social_pulse.git
cd social_pulse

# Create a virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials

Create a `.env` file in the root directory and add your details:

```env
SECRET_KEY=any-secret-string
INSTAGRAM_USERNAME=your_username
INSTAGRAPI_SESSION_B64=your_base64_string_here
INSTALOADER_SESSION_B64=your_base64_string_here
```

**Note**: To get these Base64 strings, use the external `insta_session` extraction tool to safely extract them from your local browser cookies. The app acts purely statelessly!

### 3. Run It!

```bash
python app.py
```

Open `http://localhost:5000` in your browser.

---

## 🐳 Docker (Optional)

Prefer containers? We've got you covered with a robust Nginx setup.

**Note**: To protect your IP, we don't let the container login directly. You need to generate a session first.

1. **Generate Sessions** (Locally):
   Use the `insta_session` repository to extract your Chrome cookies and generate the B64 keys.
2. **Set .env File**:
   Paste `INSTAGRAPI_SESSION_B64` and `INSTALOADER_SESSION_B64` directly into your `.env`.
3. **Run Container**:

   ```bash
   docker-compose up --build -d
   ```

   The app will be accessible at **http://localhost** (Port 80).

---

## 💡 Troubleshooting

- **Scraping failed?**
  It happens! Wait a few minutes and try again. Our hybrid engine usually self-corrects. If it consistently fails, you may need to extract fresh Base64 sessions using `insta_session`.

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

- [ ] **Multi-Platform Support**: Architecture ready for Facebook & Twitter modules.
- [ ] **Database Integration**: Migrate from CSV to SQLite/PostgreSQL.
- [ ] **Visual Dashboards**: Add chart.js visualizations for sentiment trends.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
