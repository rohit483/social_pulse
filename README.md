# Social Pulse v1

**Social Pulse** is a robust, modular web application designed for scraping and analyzing social media comments. It currently features a high-performance Instagram scraper and an advanced Sentiment Analysis engine powered by VADER, fine-tuned for social media slang and emojis.

## 🚀 Key Features

### 📸 Instagram Scraper

- **Smart Scraping**: Fetches comments from public Instagram posts using `instaloader`.
- **Reliable Login**: Implements a robust 3-tier login system:
  1. **Session File**: Loads existing session for instant access.
  2. **Direct Login**: Standard credential login.
  3. **Selenium Fallback**: Launches a headless browser to bypass complex login challenges if standard methods fail.
- **Lazy Loading**: Scraper resources (like Selenium drivers) are only initialized when needed, ensuring **instant** application startup.

### 🧠 Advanced Sentiment Analysis

- **VADER-Powered**: Uses `vaderSentiment` for superior accuracy with social media text.
- **Custom Slang Lexicon**: We've patched the sentiment engine to correctly understand modern internet slang (e.g., `fire`, `lit`, `based`, `w`) and emojis that standard libraries often misinterpret.
- **Data Integrity**: Full UTF-8 support ensures emojis and special characters are preserved perfectly.

### 📊 Data Management

- **CSV Upload**: Analyze existing datasets by uploading CSV files.
- **Export Options**: Download both raw scraped data and fully analyzed sentiment reports as CSVs.

---

## 📂 Project Structure

The project follows a clean, modular architecture for easy maintenance and scalability:

```text
Social_pulse_v1/
├── app.py                  # Main Flask Application (API & Routes)
├── requirements.txt        # Project Dependencies
├── modules/                # Core Logic Modules
│   ├── analysis/           # Sentiment Analysis Engine
│   ├── configuration/      # Config & Env Management
│   └── instagram/          # Scraper & Login Logic
├── sp_env/                 # Environment Variables Directory
│   └── .env                # Secrets (Not committed to Git)
├── static/                 # CSS & JavaScript
├── templates/              # HTML Templates
└── webdata/                # Data Storage
    ├── csv uploads/        # Uploaded files
    └── csv downloads/      # Generated reports
```

---

## 🛠️ Setup & Installation

### Prerequisites

- Python 3.8 or higher
- Google Chrome (for Selenium fallback)

### 1. Installation

Clone the repository and install dependencies:

```bash
cd Social_pulse_v1
pip install -r requirements.txt
```

### 2. Configuration

Create a specific environment folder and file for your credentials.
**Path**: `venv/.env`

Add your specific configuration details to `venv/.env`:

```env
SECRET_KEY=your_secret_key_here
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password
# Optional: Initial download folder override
DOWNLOAD_FOLDER=
```

### 3. Running the Application

Start the Flask server:

```bash
python app.py
```

Access the dashboard at: `http://127.0.0.1:5000`

---

## 🔮 Future Roadmap

- [ ] **Multi-Platform Support**: Architecture ready for Facebook & Twitter modules.
- [ ] **Database Integration**: Migrate from CSV to SQLite/PostgreSQL for persistent storage.
- [ ] **Visual Dashboards**: Add chart.js visualizations for sentiment trends.
