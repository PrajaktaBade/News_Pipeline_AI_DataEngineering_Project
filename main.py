"""
main.py — Pipeline Orchestrator
=================================
This is the main entry point. It wires together:
  1. extract.py  → fetch headlines from NewsAPI
  2. analyze.py  → run AI sentiment analysis
  3. store.py    → save results to SQLite database

Run this script to execute the full pipeline:
  python main.py
  python main.py --topic "climate change" --count 20
"""

import argparse
import sys
import os
from dotenv import load_dotenv

load_dotenv()


def run_pipeline(topic: str = None, count: int = None):
    """Execute the full ETL pipeline."""
    from extract import fetch_headlines
    from analyze import analyze_sentiment
    from store import save_results, get_stats

    topic = topic or os.getenv("NEWS_TOPIC", "technology")
    count = count or int(os.getenv("HEADLINES_COUNT", 20))

    print("=" * 55)
    print("  📰 NEWS SENTIMENT PIPELINE")
    print("=" * 55)
    print(f"  Topic  : {topic}")
    print(f"  Count  : {count}")
    print(f"  AI Mode: {os.getenv('AI_MODE', 'local')}")
    print("=" * 55)
    print()

    # ── Step 1: Extract ──────────────────────────────────────
    print("[ STEP 1 / 3 ] Extracting headlines...")
    try:
        headlines = fetch_headlines(query=topic, count=count)
    except (ValueError, ConnectionError) as e:
        print(f"\n❌ Extraction failed: {e}")
        sys.exit(1)

    if not headlines:
        print("❌ No headlines found. Try a different topic.")
        sys.exit(1)

    print()

    # ── Step 2: Analyze ──────────────────────────────────────
    print("[ STEP 2 / 3 ] Running AI sentiment analysis...")
    try:
        enriched = analyze_sentiment(headlines)
    except (ValueError, ImportError) as e:
        print(f"\n❌ Analysis failed: {e}")
        sys.exit(1)

    print()

    # ── Step 3: Store ────────────────────────────────────────
    print("[ STEP 3 / 3 ] Saving to database...")
    save_results(enriched, topic=topic)

    print()
    print("=" * 55)
    print("  ✅ PIPELINE COMPLETE!")
    print()

    # Print quick summary
    stats = get_stats()
    print(f"  Total in database : {stats['total']}")
    print(f"  Positive          : {stats['positive']}")
    print(f"  Negative          : {stats['negative']}")
    print(f"  Neutral           : {stats['neutral']}")
    print()
    print("  💡 Run the dashboard: streamlit run dashboard.py")
    print("=" * 55)

    return enriched


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the News Sentiment Pipeline")
    parser.add_argument("--topic", type=str, help="News topic to search (e.g. 'bitcoin')")
    parser.add_argument("--count", type=int, help="Number of headlines to fetch (1-100)")
    args = parser.parse_args()

    run_pipeline(topic=args.topic, count=args.count)
