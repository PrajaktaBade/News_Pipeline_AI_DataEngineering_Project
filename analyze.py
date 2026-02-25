"""
analyze.py — AI Sentiment Analysis Module
==========================================
Takes a list of headlines and adds sentiment scores using either:
  - "local"  mode: HuggingFace transformers (FREE, runs on your machine, ~500MB download)
  - "openai" mode: OpenAI GPT-4o-mini (costs ~$0.001 per 30 headlines, very cheap)

This is the "T" in ETL (Transform).
"""

import os
import json
import time
from dotenv import load_dotenv

load_dotenv()


# ─── Local Mode (HuggingFace) ─────────────────────────────────────────────────

def load_local_model():
    """
    Load a pre-trained sentiment analysis model from HuggingFace.
    First run will download ~500MB. Subsequent runs use the cached model.
    """
    try:
        from transformers import pipeline
        print("🤖 Loading local AI model (first run downloads ~500MB, please wait)...")
        # distilbert is small, fast, and accurate for sentiment
        classifier = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            truncation=True,
            max_length=512,
        )
        print("✅ Model loaded!")
        return classifier
    except ImportError:
        raise ImportError(
            "transformers or torch not installed.\n"
            "Run: pip install transformers torch"
        )


def analyze_local(headlines: list[dict]) -> list[dict]:
    """Analyze sentiment using a local HuggingFace model (no API key needed)."""
    classifier = load_local_model()
    results = []

    print(f"🔬 Analyzing {len(headlines)} headlines locally...")

    for headline in headlines:
        try:
            # Use title + description for better accuracy
            text = headline["title"]
            if headline.get("description"):
                text += ". " + headline["description"][:200]

            output = classifier(text[:512])[0]  # Model has 512 token limit

            # HuggingFace returns POSITIVE/NEGATIVE, map to lowercase + add neutral
            label = output["label"].lower()
            score = round(output["score"], 4)

            # If confidence is low (< 0.65), classify as neutral
            if score < 0.65:
                label = "neutral"
                score = round(1 - score, 4)

            results.append({
                **headline,
                "sentiment": label,
                "confidence": score,
                "ai_mode": "local",
            })

        except Exception as e:
            print(f"  ⚠️  Skipped '{headline['title'][:50]}...' — {e}")
            results.append({
                **headline,
                "sentiment": "neutral",
                "confidence": 0.5,
                "ai_mode": "local",
            })

    return results


# ─── OpenAI Mode ──────────────────────────────────────────────────────────────

def analyze_openai(headlines: list[dict]) -> list[dict]:
    """Analyze sentiment using OpenAI GPT-4o-mini (requires API key)."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("openai not installed. Run: pip install openai")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_key_here":
        raise ValueError(
            "OPENAI_API_KEY is not set!\n"
            "1. Go to https://platform.openai.com/api-keys\n"
            "2. Create a key and add it to .env as: OPENAI_API_KEY=your_key\n"
        )

    client = OpenAI(api_key=api_key)
    results = []

    print(f"🤖 Analyzing {len(headlines)} headlines with OpenAI GPT-4o-mini...")

    for i, headline in enumerate(headlines):
        try:
            prompt = f"""Analyze the sentiment of this news headline and description.
Return ONLY valid JSON, no other text.
Format: {{"sentiment": "positive" | "negative" | "neutral", "confidence": 0.0-1.0, "reason": "one short sentence"}}

Headline: {headline['title']}
Description: {headline.get('description', '')[:200]}"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=100,
            )

            raw = response.choices[0].message.content.strip()
            parsed = json.loads(raw)

            results.append({
                **headline,
                "sentiment": parsed.get("sentiment", "neutral"),
                "confidence": round(float(parsed.get("confidence", 0.5)), 4),
                "reason": parsed.get("reason", ""),
                "ai_mode": "openai",
            })

            # Small delay to avoid hitting rate limits
            if i > 0 and i % 10 == 0:
                time.sleep(1)
                print(f"  Processed {i}/{len(headlines)}...")

        except json.JSONDecodeError:
            print(f"  ⚠️  JSON parse error for: '{headline['title'][:50]}'")
            results.append({**headline, "sentiment": "neutral", "confidence": 0.5, "ai_mode": "openai"})
        except Exception as e:
            print(f"  ⚠️  Error for '{headline['title'][:50]}': {e}")
            results.append({**headline, "sentiment": "neutral", "confidence": 0.5, "ai_mode": "openai"})

    return results


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def analyze_sentiment(headlines: list[dict]) -> list[dict]:
    """
    Analyze sentiment for a list of headlines.
    Mode is controlled by AI_MODE in .env ("local" or "openai").
    """
    mode = os.getenv("AI_MODE", "local").lower()

    if mode == "openai":
        enriched = analyze_openai(headlines)
    else:
        enriched = analyze_local(headlines)

    # Print summary
    sentiments = [r["sentiment"] for r in enriched]
    pos = sentiments.count("positive")
    neg = sentiments.count("negative")
    neu = sentiments.count("neutral")
    print(f"\n📊 Results: {pos} positive | {neg} negative | {neu} neutral")

    return enriched


if __name__ == "__main__":
    # Test this module directly: python analyze.py
    test_headlines = [
        {"title": "Tech stocks soar to record highs as AI boom continues", "description": "", "source": "Test", "published_at": "", "url": ""},
        {"title": "Global recession fears grow amid rising interest rates", "description": "", "source": "Test", "published_at": "", "url": ""},
        {"title": "Scientists publish new research on climate patterns", "description": "", "source": "Test", "published_at": "", "url": ""},
    ]
    results = analyze_sentiment(test_headlines)
    for r in results:
        print(f"  {r['sentiment'].upper():8} ({r['confidence']:.0%}) — {r['title']}")
