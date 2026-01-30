# Social Pulse

**Social Pulse** is a robust, modular web application designed for scraping and analyzing social media comments. It features a fail-proof **4-tier Instagram login system** and an advanced **Sentiment Analysis engine** powered by VADER, fine-tuned for modern social media slang.

## 🚀 Key Features

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
├── venv/                    # Virtual Environment & Secrets (gitignored)
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

- Python 3.9 or higher

### 1. Clone the Repository

```bash
git clone https://github.com/rohit483/social_pulse.git
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
   # Note: Wrap password in single or double quotes to handle special characters (#, $)
   ```

### 6. Run the Application

```bash
python app.py
```

Access the dashboard at: `http://127.0.0.1:5000`

---

## 💡 Login Troubleshooting

**"Wrong Password" Error?**

- Ensure your password in `.env` is wrapped in quotes: `INSTAGRAM_PASSWORD='pass#word'`
- The app logs a masked version of your password (e.g., `p******`) on startup. Check the console to verify it loaded correctly.

**"Login Fails" on Instaloader?**

- Don't worry! The app will automatically switch to **Instagrapi**. Look for "Attempting Fallback Login" in the logs.

**First Run Delay?**

- The first login might take 5-10 seconds. Subsequent runs will use the saved session files and be instant.

---

## 🔮 Future Roadmap

- [ ] **Multi-Platform Support**: Architecture ready for Facebook & Twitter modules.
- [ ] **Database Integration**: Migrate from CSV to SQLite/PostgreSQL.
- [ ] **Visual Dashboards**: Add chart.js visualizations for sentiment trends.
