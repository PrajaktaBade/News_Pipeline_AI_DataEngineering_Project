"""
extract.py — Data Extraction Module
====================================
Fetches news headlines from NewsAPI and returns them as a list of dicts.
This is the "E" in ETL (Extract, Transform, Load).
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


def fetch_headlines(query: str = None, count: int = None) -> list[dict]:
    """
    Fetch news headlines from NewsAPI.

    Args:
        query: Search term (e.g. "artificial intelligence", "bitcoin", "climate")
        count: Number of articles to fetch (max 100 on free tier)

    Returns:
        List of dicts with keys: title, source, published_at, url, description
    """
    query = query or os.getenv("NEWS_TOPIC", "technology")
    count = count or int(os.getenv("HEADLINES_COUNT", 20))
    api_key = os.getenv("NEWS_API_KEY")

    if not api_key or api_key == "your_newsapi_key_here":
        raise ValueError(
            "NEWS_API_KEY is not set!\n"
            "1. Go to https://newsapi.org/register (free)\n"
            "2. Copy your API key\n"
            "3. Add it to your .env file as: NEWS_API_KEY=your_key\n"
        )

    # NewsAPI /everything endpoint - searches all articles
    url = "https://newsapi.org/v2/everything"

    # Only fetch articles from the last 7 days (free tier limit is 1 month)
    from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    params = {
        "q": query,
        "pageSize": min(count, 100),  # API max is 100
        "language": "en",
        "sortBy": "publishedAt",       # Most recent first
        "from": from_date,
        "apiKey": api_key,
    }

    print(f"🔍 Fetching {count} headlines for topic: '{query}'...")

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Raises an error for HTTP 4xx/5xx
    except requests.exceptions.ConnectionError:
        raise ConnectionError("No internet connection. Check your network and try again.")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise ValueError("Invalid API key. Check your NEWS_API_KEY in .env")
        raise e

    data = response.json()

    if data.get("status") != "ok":
        raise ValueError(f"NewsAPI error: {data.get('message', 'Unknown error')}")

    articles = data.get("articles", [])

    # Clean and normalize the data
    headlines = []
    for article in articles:
        title = article.get("title", "").strip()

        # Skip articles with missing or placeholder titles
        if not title or title == "[Removed]":
            continue

        headlines.append({
            "title": title,
            "source": article.get("source", {}).get("name", "Unknown"),
            "published_at": article.get("publishedAt", ""),
            "url": article.get("url", ""),
            "description": article.get("description", "") or "",
        })

    print(f"✅ Fetched {len(headlines)} valid headlines.")
    return headlines


if __name__ == "__main__":
    # Test this module directly: python extract.py
    headlines = fetch_headlines()
    print("\n--- Sample Headlines ---")
    for i, h in enumerate(headlines[:5], 1):
        print(f"{i}. [{h['source']}] {h['title']}")
