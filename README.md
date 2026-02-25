# 📰 News Sentiment Pipeline
### AI + Data Engineering Project

Build a real data pipeline that fetches news, runs AI sentiment analysis, stores results in a database, and shows them in a live dashboard.

---

## 🗂️ Project Structure

```
news_pipeline/
├── .env              ← API  keys (never commit this to Git!)
├── requirements.txt  ← Python packages needed
│
├── extract.py        ← STEP 1: Fetch headlines from NewsAPI
├── analyze.py        ← STEP 2: Run AI sentiment analysis
├── store.py          ← STEP 3: Save results to SQLite database
├── main.py           ← Runs all 3 steps in sequence
│
├── dashboard.py      ← Interactive web dashboard (Streamlit)
├── news.db           ← Database file (created automatically)
└── README.md         ← This file
```

---

## ⚡ Quick Start (5 steps)

### Step 1 — Get a free NewsAPI key (2 minutes)

1. Go to **https://newsapi.org/register**
2. Sign up with your email (free, no credit card)
3. Copy your API key from the dashboard

### Step 2 — Set up your environment

Open a terminal in the `news_pipeline/` folder, then:

```bash
# Create a virtual environment (keeps your packages isolated)
python -m venv venv

# Activate it
source venv/bin/activate       # Mac / Linux
venv\Scripts\activate          # Windows (Command Prompt)
.\venv\Scripts\Activate.ps1    # Windows (PowerShell)

# Install all required packages
pip install -r requirements.txt
```

> 💡 You'll know the virtual environment is active when you see `(venv)` at the start of your terminal prompt.

### Step 3 — Add your API key

Open `.env` in any text editor and add you API keys:

```
NEWS_API_KEY=abc123yourkeyhere
NEWS_TOPIC=artificial intelligence
HEADLINES_COUNT=25
AI_MODE=local
```

### Step 4 — Run the pipeline

```bash
python main.py
```

You should see output like:
```
=======================================================
  📰 NEWS SENTIMENT PIPELINE
=======================================================
  Topic  : artificial intelligence
  Count  : 25
  AI Mode: local
=======================================================

[ STEP 1 / 3 ] Extracting headlines...
✅ Fetched 25 valid headlines.

[ STEP 2 / 3 ] Running AI sentiment analysis...
🤖 Loading local AI model (first run downloads ~500MB)...
✅ Model loaded!
🔬 Analyzing 25 headlines locally...
📊 Results: 12 positive | 8 negative | 5 neutral

[ STEP 3 / 3 ] Saving to database...
💾 Saved 25 rows to database.

=======================================================
  ✅ PIPELINE COMPLETE!
  Total in database : 25
  Positive          : 12
  Negative          : 8
  Neutral           : 5

  💡 Run the dashboard: streamlit run dashboard.py
=======================================================
```

> ⚠️ **First run only**: The AI model (~500MB) will be downloaded automatically. This takes 1-3 minutes depending on your internet speed. Subsequent runs use the cached model and are instant.

### Step 5 — Open the dashboard

```bash
streamlit run dashboard.py
```

Your browser will automatically open **http://localhost:8501** with the live dashboard!

---

## 🎛️ Configuration Options

Edit your `.env` file to customize behavior:

| Variable | Description | Example |
|----------|-------------|---------|
| `NEWS_API_KEY` | Your NewsAPI key (required) | `abc123...` |
| `NEWS_TOPIC` | Topic to search for | `bitcoin`, `climate change`, `football` |
| `HEADLINES_COUNT` | How many articles to fetch (1–100) | `30` |
| `AI_MODE` | `local` (free) or `openai` (better accuracy) | `local` |
| `OPENAI_API_KEY` | OpenAI key (only needed for openai mode) | `sk-...` |

---

## 🤖 AI Modes Explained

### Local Mode (Default — Free)
Uses a **DistilBERT** model from HuggingFace that runs entirely on your computer.
- ✅ Free forever
- ✅ No API key needed
- ✅ Works offline after first download
- ⚠️ Downloads ~500MB on first run
- ⚠️ Slightly less accurate than GPT

Set in `.env`: `AI_MODE=local`

### OpenAI Mode (Better Accuracy)
Uses **GPT-4o-mini** for higher-quality analysis with reasoning.
- ✅ More accurate, provides explanations
- ✅ Very cheap (~$0.001 per 30 headlines)
- ⚠️ Requires OpenAI API key and internet

Set in `.env`: `AI_MODE=openai`

---

## 🔧 Running with Different Topics

```bash
# Override topic from command line (doesn't change .env)
python main.py --topic "bitcoin"
python main.py --topic "climate change" --count 50
python main.py --topic "Premier League"
```

---

## 📊 Dashboard Features

| Feature | Description |
|---------|-------------|
| KPI metrics | Total, positive %, negative %, confidence |
| Pie chart | Sentiment distribution |
| Bar chart | Sentiment by news source |
| Timeline | How sentiment changes over multiple runs |
| Data table | All headlines with color-coded sentiment |
| CSV export | Download your data |
| Run pipeline | Trigger new pipeline run from the dashboard |
| Filters | Filter by topic, sentiment, or source |

---

## 🚀 Stretch Goals

### 1. Schedule automatic runs (cron job)
Run the pipeline every hour without manual intervention:

```bash
# Open crontab editor
crontab -e

# Add this line to run every hour:
0 * * * * /path/to/venv/bin/python /path/to/news_pipeline/main.py
```

### 2. Track multiple topics
```bash
# Run multiple times with different topics to compare
python main.py --topic "OpenAI"
python main.py --topic "Google AI"
python main.py --topic "Microsoft AI"
# Then filter by topic in the dashboard!
```

### 3. Upgrade to PostgreSQL (production database)
Change one line in `store.py`:
```python
# Replace:
engine = sa.create_engine(f"sqlite:///{DB_PATH}")

# With:
engine = sa.create_engine("postgresql://user:password@localhost/newsdb")
```

### 4. Add email alerts
Send yourself an email when sentiment goes very negative:
```python
import smtplib
if neg_pct > 0.7:
    # send alert email
```

### 5. Deploy your dashboard
- **Streamlit Community Cloud** (free): https://share.streamlit.io
- **Render** (free tier): https://render.com
- **Railway**: https://railway.app

---

## 🐛 Troubleshooting

- **`NEWS_API_KEY is not set`**
→ Make sure you renamed added your real keyin `.env` file.

- **`No module named 'streamlit'`**
→ Run `pip install -r requirements.txt` and make sure your venv is activated.

- **`0 articles fetched`**
→ Try a more common topic like `technology` or `sports`. Some niche topics have few results.

- **Pipeline runs but model download is slow**
→ The first run downloads a 500MB AI model. This is normal. Future runs are instant.

- **Dashboard shows "No data yet"**
→ Run `python main.py` first to populate the database.

---

## 🧠 What I Learned

| Concept | Where You Learn It |
|---------|-------------------|
| REST API calls | `extract.py` — fetching from NewsAPI |
| Data cleaning | `extract.py` — filtering bad records |
| AI/NLP models | `analyze.py` — sentiment analysis |
| Prompt engineering | `analyze.py` — OpenAI mode prompts |
| SQL databases | `store.py` — SQLAlchemy + SQLite |
| ETL pipelines | `main.py` — orchestrating all 3 steps |
| Data visualization | `dashboard.py` — Plotly + Streamlit |
| CLI tools | `main.py` — argparse for arguments |
| Environment variables | `.env` — keeping secrets safe |
| Python packaging | `requirements.txt` — dependency management |
