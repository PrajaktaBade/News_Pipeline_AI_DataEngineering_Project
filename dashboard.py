"""
dashboard.py — Streamlit Dashboard
=====================================
Interactive web dashboard to explore your sentiment data.

Run with:
  streamlit run dashboard.py

Then open http://localhost:8501 in your browser.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page config — must be the first Streamlit call
st.set_page_config(
    page_title="News Sentiment Dashboard",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Load Data ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)  # Cache for 30 seconds, then refresh
def load_data():
    """Load data from the database."""
    try:
        from store import load_all
        df = load_all()
        if not df.empty:
            df["fetched_at"] = pd.to_datetime(df["fetched_at"])
            df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📰 News Sentiment")
    st.markdown("---")

    df_full = load_data()

    if df_full.empty:
        st.warning("No data yet! Run the pipeline first:\n```\npython main.py\n```")
        st.stop()

    # Filters
    st.subheader("🔍 Filters")

    topics = ["All"] + sorted(df_full["topic"].dropna().unique().tolist())
    selected_topic = st.selectbox("Topic", topics)

    sentiments = ["All", "positive", "negative", "neutral"]
    selected_sentiment = st.selectbox("Sentiment", sentiments)

    sources = ["All"] + sorted(df_full["source"].dropna().unique().tolist())
    selected_source = st.selectbox("Source", sources)

    st.markdown("---")
    st.subheader("⚡ Run Pipeline")
    new_topic = st.text_input("New topic to analyze:", placeholder="e.g. bitcoin")
    new_count = st.slider("Headlines to fetch", 5, 50, 20)

    if st.button("🚀 Run Now", use_container_width=True):
        with st.spinner("Running pipeline..."):
            try:
                import subprocess, sys
                cmd = [sys.executable, "main.py"]
                if new_topic:
                    cmd += ["--topic", new_topic]
                cmd += ["--count", str(new_count)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    st.success("✅ Pipeline complete!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"Pipeline failed:\n{result.stderr}")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    if st.button("🗑️ Clear Database", use_container_width=True):
        if st.session_state.get("confirm_clear"):
            from store import clear_db
            clear_db()
            st.cache_data.clear()
            st.session_state["confirm_clear"] = False
            st.rerun()
        else:
            st.session_state["confirm_clear"] = True
            st.warning("Click again to confirm deletion of all data.")

# ─── Apply Filters ────────────────────────────────────────────────────────────

df = df_full.copy()
if selected_topic != "All":
    df = df[df["topic"] == selected_topic]
if selected_sentiment != "All":
    df = df[df["sentiment"] == selected_sentiment]
if selected_source != "All":
    df = df[df["source"] == selected_source]

# ─── Main Dashboard ───────────────────────────────────────────────────────────

st.title("📰 News Sentiment Dashboard")
st.caption(f"Last updated: {df_full['fetched_at'].max().strftime('%Y-%m-%d %H:%M')} · {len(df_full)} total records")

# ── KPI Metrics ──────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

total = len(df)
pos_count = (df["sentiment"] == "positive").sum()
neg_count = (df["sentiment"] == "negative").sum()
neu_count = (df["sentiment"] == "neutral").sum()
avg_conf = df["confidence"].mean() if total > 0 else 0

col1.metric("Total Headlines", total)
col2.metric("Positive 🟢", pos_count, f"{pos_count/total:.0%}" if total else "")
col3.metric("Negative 🔴", neg_count, f"-{neg_count/total:.0%}" if total else "", delta_color="inverse")
col4.metric("Neutral ⚪", neu_count, f"{neu_count/total:.0%}" if total else "")
col5.metric("Avg Confidence", f"{avg_conf:.0%}")

st.markdown("---")

# ── Charts Row ───────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Sentiment Distribution")
    if total > 0:
        sentiment_counts = df["sentiment"].value_counts().reset_index()
        sentiment_counts.columns = ["sentiment", "count"]

        colors = {"positive": "#22c55e", "negative": "#ef4444", "neutral": "#94a3b8"}
        sentiment_counts["color"] = sentiment_counts["sentiment"].map(colors)

        fig = px.pie(
            sentiment_counts,
            values="count",
            names="sentiment",
            color="sentiment",
            color_discrete_map=colors,
            hole=0.5,
        )
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
        st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader("Top Sources")
    if total > 0:
        source_sentiment = df.groupby(["source", "sentiment"]).size().reset_index(name="count")
        top_sources = df["source"].value_counts().head(8).index.tolist()
        source_sentiment = source_sentiment[source_sentiment["source"].isin(top_sources)]

        colors = {"positive": "#22c55e", "negative": "#ef4444", "neutral": "#94a3b8"}
        fig2 = px.bar(
            source_sentiment,
            x="source",
            y="count",
            color="sentiment",
            color_discrete_map=colors,
            barmode="stack",
        )
        fig2.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320,
                           xaxis_tickangle=-30, legend_title="")
        st.plotly_chart(fig2, use_container_width=True)

# ── Timeline ─────────────────────────────────────────────────────────────────
st.subheader("Sentiment Over Time")
if total > 0:
    df["date"] = df["fetched_at"].dt.date
    timeline = df.groupby(["date", "sentiment"]).size().reset_index(name="count")

    colors = {"positive": "#22c55e", "negative": "#ef4444", "neutral": "#94a3b8"}
    fig3 = px.line(
        timeline,
        x="date",
        y="count",
        color="sentiment",
        color_discrete_map=colors,
        markers=True,
    )
    fig3.update_layout(margin=dict(t=10, b=10), height=250, legend_title="")
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# ── Data Table ───────────────────────────────────────────────────────────────
st.subheader(f"📋 Headlines ({total})")

if total > 0:
    # Color sentiment column
    def color_sentiment(val):
        colors_map = {"positive": "#166534", "negative": "#7f1d1d", "neutral": "#1e3a5f"}
        bg = colors_map.get(val, "#1e293b")
        return f"background-color: {bg}; color: white; border-radius: 4px; padding: 2px 6px;"

    display_cols = ["title", "source", "sentiment", "confidence", "published_at", "topic"]
    display_cols = [c for c in display_cols if c in df.columns]

    display_df = df[display_cols].copy()
    display_df["confidence"] = display_df["confidence"].map("{:.0%}".format)

    styled = display_df.style.applymap(color_sentiment, subset=["sentiment"])
    st.dataframe(styled, use_container_width=True, height=400)

    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        "⬇️ Download as CSV",
        data=csv,
        file_name=f"news_sentiment_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
