# Social Pulse

**Social Pulse** is a robust, modular web application designed for scraping and analyzing social media comments. It features a fail-proof **4-tier Instagram login system** and an advanced **Sentiment Analysis engine** powered by VADER, fine-tuned for modern social media slang.

## 🚀 Key Features

### 📸 Fail-Proof Instagram Scraper

- **Smart Scraping**: Fetches comments from public Instagram posts using `instaloader`.
- **4-Tier Login System**: Automatically tries methods in order until successful:
  1. **Session File**: Loads existing session for instant, captcha-free access.
  2. **Direct Login**: Standard username/password authentication.
  3. **Selenium Fallback**: Launches a headless browser to bypass complex login challenges.
  4. **Browser Cookies**: Auto-detects and imports your logged-in session from Chrome, Firefox, or Edge (Clone-friendly feature!).
- **Session Warm-up**: Automatically "warms up" fresh sessions with dummy API calls to prevent "Something went wrong" errors on the first scrape.
- **Lazy Loading**: Scraper resources are only initialized when the scrape button is clicked, ensuring instant app startup.

### 🧠 Advanced Sentiment Analysis

- **VADER-Powered**: Uses `vaderSentiment` for superior accuracy with social media text.
- **Custom Slang Lexicon**: Patched engine understands Gen-Z slang (e.g., `fire`, `lit`, `based`, `w`, `no cap`) and emojis that standard libraries often miss.
- **Data Integrity**: Full UTF-8 support ensures emojis and special characters are preserved.

### 📊 Data Management

- **CSV Upload**: Analyze existing datasets by uploading CSV files.
- **Export Options**: Download both raw scraped data and fully analyzed sentiment reports.

---

## 📂 Project Structure

```text
social_pulse/
├── app.py                  # Main Flask Application
├── requirements.txt        # Project Dependencies
├── modules/                # Core Logic Modules
│   ├── analysis/           # Sentiment Engine (VADER + Custom Lexicon)
│   ├── configuration/      # Config & Env Management
│   └── instagram/          # Scraper, Login Logic & Browser Cookie Import
├── env/                    # Virtual Environment & Secrets (gitignored)
│   └── .env                # Secrets file
├── static/                 # Assets (CSS/JS)
├── templates/              # HTML Templates
└── webdata/                # Auto-generated Data Storage
    ├── csv uploads/        # Uploaded files
    └── csv downloads/      # Generated reports
```

---

## 🛠️ Installation & Setup

Follow these steps to set up the project locally.

### Prerequisites

- Python 3.8 or higher
- Google Chrome (optional, for Selenium fallback)

### 1. Clone the Repository

```bash
git clone https://github.com/AbhiJeet4241/social_pulse.git
cd social_pulse
```

### 2. Create Virtual Environment

It is recommended to use a virtual environment to manage dependencies. You can name it `env`, `venv`, or `sp_env`.

```bash
# Windows
python -m venv env

# Mac/Linux
python3 -m venv env
```

### 3. Activate Virtual Environment

```bash
# Windows
.\env\Scripts\activate

# Mac/Linux
source env/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configuration

1. Navigate to your environment folder.
2. Create a new file named `.env`.
3. Add the following configuration variables:

   ```env
   SECRET_KEY=dev-secret-key-123
   INSTAGRAM_USERNAME=your_instagram_username
   INSTAGRAM_PASSWORD="your_instagram_password"
   # Note: Wrap password in double quotes if it has special characters (#, $)
   ```

### 6. Run the Application

```bash
python app.py
```

Access the dashboard at: `http://127.0.0.1:5000`

---

## 💡 Login Troubleshooting

**"Wrong Password" Error?**

- Ensure your password in `.env` is wrapped in double quotes: `INSTAGRAM_PASSWORD="pass#word"`
- **Alternative**: Simply login to Instagram in your Chrome/Edge browser. The app will automatically detect (Step 4) and import your session!

**First Run Delay?**

- The first login might take 5-10 seconds as it "warms up" the session. Subsequent runs will use the saved session file and be instant.

**Cloning this Repo?**

- You do not need to copy any session files. Just run the app, and it will create a fresh session on your machine using your credentials or browser cookies.

---

## 🔮 Future Roadmap

- [ ] **Multi-Platform Support**: Architecture ready for Facebook & Twitter modules.
- [ ] **Database Integration**: Migrate from CSV to SQLite/PostgreSQL.
- [ ] **Visual Dashboards**: Add chart.js visualizations for sentiment trends.
