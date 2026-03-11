import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import concurrent.futures
from tqdm import tqdm
import time
import logging
import numpy as np
from io import StringIO
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF
import tempfile
import os
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from portfolio_manager import PortfolioManager

# Initialize Portfolio Manager
pm = PortfolioManager()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Set page config
st.set_page_config(
    page_title="Analyst Conviction Dashboard", layout="wide", page_icon="📈"
)

# --- Data Fetching Helper Functions ---


def get_sp500_tickers():
    """Fetches S&P 500 tickers."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        tables = pd.read_html(StringIO(response.text))

        df = None
        for table in tables:
            if "Symbol" in table.columns:
                df = table
                break

        if df is None:
            return []

        tickers = df["Symbol"].tolist()
        return [t.replace(".", "-") for t in tickers]
    except Exception as e:
        logging.error(f"Error fetching S&P 500 tickers: {e}")
        return []


def get_sp400_tickers():
    """Fetches S&P 400 tickers."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        tables = pd.read_html(StringIO(response.text))

        df = None
        for table in tables:
            if "Symbol" in table.columns or "Ticker symbol" in table.columns:
                df = table
                break

        if df is None:
            for table in tables:
                if "Ticker Symbol" in table.columns:
                    df = table
                    break

        if df is None:
            return []

        col = "Symbol" if "Symbol" in df.columns else "Ticker Symbol"
        tickers = df[col].tolist()
        return [t.replace(".", "-") for t in tickers]
    except Exception as e:
        logging.error(f"Error fetching S&P 400 tickers: {e}")
        return []


def get_combined_tickers():
    """Combines S&P 500 and S&P 400 tickers."""
    sp500 = get_sp500_tickers()
    sp400 = get_sp400_tickers()
    combined = list(set(sp500 + sp400))
    return combined


def calculate_rsi(series, period=14):
    """Calculate RSI manually."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)

    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


import random

# Suppress yfinance error logging
logger = logging.getLogger("yfinance")
logger.setLevel(logging.CRITICAL)


def fetch_ticker_data(ticker):
    """Fetches data for a single ticker including TA with retries."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Rate limit delay
            time.sleep(random.uniform(0.5, 2.0))

            ticker = ticker.replace(".", "-")
            stock = yf.Ticker(ticker)

            # 1. Get Info & Recommendations
            try:
                info = stock.info
            except Exception:
                # If info fails (e.g. 404), it's likely a bad ticker. Don't retry.
                return None

            rec_summary = stock.get_recommendations_summary()

            # Parse Recommendations
            if rec_summary is not None and not rec_summary.empty:
                if "period" in rec_summary.columns:
                    current_rec = rec_summary[rec_summary["period"] == "0m"]
                    latest_rec = (
                        current_rec.iloc[0]
                        if not current_rec.empty
                        else rec_summary.iloc[0]
                    )
                else:
                    latest_rec = rec_summary.iloc[0]

                strong_buy = latest_rec.get("strongBuy", 0)
                buy = latest_rec.get("buy", 0)
                hold = latest_rec.get("hold", 0)
                sell = latest_rec.get("sell", 0)
                strong_sell = latest_rec.get("strongSell", 0)
                total_analysts = strong_buy + buy + hold + sell + strong_sell
            else:
                total_analysts = info.get("numberOfAnalystOpinions", 0)
                if total_analysts == 0:
                    return None
                strong_buy, buy, hold, sell, strong_sell = 0, 0, 0, 0, 0

            current_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
            target_mean = info.get("targetMeanPrice", 0)
            sector = info.get("sector", "Unknown")
            industry = info.get("industry", "Unknown")
            peg_ratio = info.get("pegRatio", None)
            beta = info.get("beta", None)

            # 2. News Sentiment Analysis
            avg_sentiment = 0
            news_risk = False
            try:
                news = stock.news
                if news:
                    sia = SentimentIntensityAnalyzer()
                    sentiments = []
                    for item in news[:10]:  # Analyze top 10 headlines
                        title = item.get("title")
                        if not title and "content" in item:
                            title = item["content"].get("title")

                        if title:
                            score = sia.polarity_scores(title)["compound"]
                            sentiments.append(score)

                    if sentiments:
                        avg_sentiment = np.mean(sentiments)
            except Exception as e:
                # logging.error(f"Error analyzing sentiment for {ticker}: {e}")
                pass

            # 3. Get Historical Data for TA
            # Fetch 1 year to ensure enough data for SMA 200
            hist = stock.history(period="1y")

            rsi = None
            sma_50 = None
            sma_200 = None

            if not hist.empty and len(hist) > 14:
                # Calculate RSI Manually
                close_prices = hist["Close"]
                rsi_series = calculate_rsi(close_prices)
                rsi = rsi_series.iloc[-1]

                # Calculate SMA Manually
                if len(hist) >= 50:
                    sma_50 = close_prices.rolling(window=50).mean().iloc[-1]

                if len(hist) >= 200:
                    sma_200 = close_prices.rolling(window=200).mean().iloc[-1]

            return {
                "Ticker": ticker,
                "Company Name": info.get("longName", ticker),
                "Sector": sector,
                "Industry": industry,
                "Strong Buy": strong_buy,
                "Buy": buy,
                "Hold": hold,
                "Sell": sell,
                "Strong Sell": strong_sell,
                "Total Analysts": total_analysts,
                "Current Price": current_price,
                "Analyst Price Target": target_mean,
                "PEG Ratio": peg_ratio,
                "Beta": beta,
                "RSI": rsi,
                "SMA_50": sma_50,
                "SMA_50": sma_50,
                "SMA_200": sma_200,
                "News Sentiment": avg_sentiment,
            }

        except Exception as e:
            # Check for 404 or specific yfinance errors that shouldn't be retried
            error_str = str(e)
            if "404" in error_str or "Not Found" in error_str:
                return None

            if attempt < max_retries - 1:
                time.sleep(2**attempt)  # Exponential backoff
                continue
            return None
    return None


def calculate_conviction_score(df):
    """Calculates the Conviction Score with TA modifiers."""

    # Filter: Exclude < 5 analysts
    df = df[df["Total Analysts"] >= 5].copy()

    if df.empty:
        return df

    # 1. Analyst Consensus (40%)
    df["Consensus Ratio"] = (df["Strong Buy"] + df["Buy"]) / df["Total Analysts"]
    df["Score_Consensus"] = df["Consensus Ratio"] * 40

    # 2. Implied Upside (40%)
    df["Implied Upside Raw"] = (df["Analyst Price Target"] - df["Current Price"]) / df[
        "Current Price"
    ]
    df["Score_Upside"] = df["Implied Upside Raw"].apply(
        lambda x: min(max(x, 0), 0.5) / 0.5 * 40 if pd.notnull(x) else 0
    )

    # 3. Analyst Volume (20%)
    max_analysts = df["Total Analysts"].max()
    df["Score_Volume"] = (df["Total Analysts"] / max_analysts) * 20

    # 4. Penalties & Boosts

    # Beta > 2.0 -> -10 points
    df["Penalty_Beta"] = df["Beta"].apply(
        lambda x: 10 if pd.notnull(x) and x > 2.0 else 0
    )

    # PEG > 3.0 -> -10 points, PEG < 0 -> -5 points
    def calculate_peg_penalty(peg):
        if pd.isnull(peg):
            return 0
        if peg > 3.0:
            return 10
        if peg < 0:
            return 5
        return 0

    df["Penalty_PEG"] = df["PEG Ratio"].apply(calculate_peg_penalty)

    # News Sentiment Modifier
    # < -0.05 -> -15 points (Safety Valve)
    # > 0.05 -> +5 points (Confirmation)
    def calculate_sentiment_score(score):
        if score < -0.05:
            return -15
        if score > 0.05:
            return 5
        return 0

    df["Score_Sentiment"] = df["News Sentiment"].apply(calculate_sentiment_score)

    # News Risk Flag (< -0.5)
    df["News Risk"] = df["News Sentiment"].apply(
        lambda x: "⚠️ NEWS RISK" if x < -0.5 else ""
    )

    # TA Modifiers
    # Boost: Strong Buy (Consensus > 0.7) AND RSI in [30, 45] -> "Dip Buying" (+10)
    # Penalty: RSI > 75 -> "Overextended" (-10)

    def calculate_ta_score(row):
        score_adj = 0
        rsi = row["RSI"]
        if pd.notnull(rsi):
            if rsi > 75:
                score_adj -= 10  # Overbought penalty
            elif 30 <= rsi <= 45 and row["Consensus Ratio"] >= 0.7:
                score_adj += 10  # Dip Buying boost
        return score_adj

    df["Score_TA"] = df.apply(calculate_ta_score, axis=1)

    # Total Score
    df["Conviction Score"] = (
        df["Score_Consensus"]
        + df["Score_Upside"]
        + df["Score_Volume"]
        - df["Penalty_Beta"]
        - df["Penalty_PEG"]
        + df["Score_TA"]
        + df["Score_Sentiment"]
    )

    # Clip score
    df["Conviction Score"] = df["Conviction Score"].clip(0, 100)

    # Formatting & Extra Cols
    df["Implied Upside %"] = df["Implied Upside Raw"].apply(
        lambda x: f"+{x * 100:.1f}%" if x > 0 else f"{x * 100:.1f}%"
    )
    df["Analyst Rating"] = (
        df["Strong Buy"] * 1
        + df["Buy"] * 2
        + df["Hold"] * 3
        + df["Sell"] * 4
        + df["Strong Sell"] * 5
    ) / df["Total Analysts"]
    df["Analyst Rating"] = df["Analyst Rating"].round(2)

    # Trend Status
    def get_trend(row):
        price = row["Current Price"]
        sma200 = row["SMA_200"]
        if pd.isnull(sma200) or pd.isnull(price):
            return "N/A"
        return "Uptrend 🟢" if price > sma200 else "Downtrend 🔴"

    df["Trend"] = df.apply(get_trend, axis=1)

    return df


@st.cache_data(ttl=3600 * 12)  # Cache for 12 hours
def load_data():
    """Fetches and processes data for all tickers."""
    tickers = get_combined_tickers()
    if not tickers:
        return pd.DataFrame()

    # 1. Identify Stale Tickers
    stale_tickers = pm.get_stale_tickers(tickers, ttl_minutes=720)  # 12 hours TTL
    fresh_tickers = list(set(tickers) - set(stale_tickers))

    results = []

    # 2. Load Fresh Data from DB
    if fresh_tickers:
        cached_data_map = pm.get_market_data(fresh_tickers)
        for ticker, data in cached_data_map.items():
            results.append(data)

    # 3. Fetch Stale Data
    if stale_tickers:
        progress_bar = st.progress(0)
        status_text = st.empty()

        chunk_size = 10
        total_stale = len(stale_tickers)
        fetched_data = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_ticker_data, t): t for t in stale_tickers}

            completed = 0
            for future in concurrent.futures.as_completed(futures):
                ticker = futures[future]
                try:
                    data = future.result()
                    if data:
                        fetched_data.append(data)
                        results.append(data)
                except Exception as e:
                    pass

                completed += 1
                if completed % chunk_size == 0 or completed == total_stale:
                    progress = completed / total_stale
                    progress_bar.progress(progress)
                    status_text.text(
                        f"Updating data: {completed}/{total_stale} tickers processed..."
                    )

        # Save new data to DB
        pm.save_market_data(fetched_data)

        progress_bar.empty()
        status_text.empty()

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)
    df = calculate_conviction_score(df)
    df = df.sort_values(by="Conviction Score", ascending=False)
    df["Rank"] = range(1, len(df) + 1)

    return df


# --- Visualization Functions ---


def plot_financial_chart(ticker):
    """Plots interactive candlestick chart with SMA and RSI."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")

        if hist.empty:
            st.warning(f"No historical data found for {ticker}")
            return

        # Calculate Indicators
        hist["SMA_50"] = hist["Close"].rolling(window=50).mean()
        hist["SMA_200"] = hist["Close"].rolling(window=200).mean()
        hist["RSI"] = calculate_rsi(hist["Close"])

        # Create Subplots
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            subplot_titles=(f"{ticker} Price & SMA", "RSI (14)"),
        )

        # Candlestick
        fig.add_trace(
            go.Candlestick(
                x=hist.index,
                open=hist["Open"],
                high=hist["High"],
                low=hist["Low"],
                close=hist["Close"],
                name="Price",
            ),
            row=1,
            col=1,
        )

        # SMA 50
        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist["SMA_50"],
                line=dict(color="blue", width=1.5),
                name="SMA 50",
            ),
            row=1,
            col=1,
        )

        # SMA 200
        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist["SMA_200"],
                line=dict(color="red", width=1.5),
                name="SMA 200",
            ),
            row=1,
            col=1,
        )

        # RSI
        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist["RSI"],
                line=dict(color="purple", width=1.5),
                name="RSI",
            ),
            row=2,
            col=1,
        )

        # RSI Levels
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

        # Layout
        fig.update_layout(
            height=600,
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            showlegend=True,
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error plotting chart for {ticker}: {e}")


def plot_sector_heatmap(df):
    """Plots sector strength analysis."""
    # Filter out Unknown sector
    clean_df = df[df["Sector"] != "Unknown"].copy()

    sector_stats = (
        clean_df.groupby("Sector")
        .agg({"Conviction Score": "mean", "Consensus Ratio": "mean", "Ticker": "count"})
        .reset_index()
    )

    sector_stats = sector_stats.sort_values(by="Conviction Score", ascending=False)

    fig = go.Figure(
        go.Bar(
            x=sector_stats["Sector"],
            y=sector_stats["Conviction Score"],
            marker=dict(color=sector_stats["Conviction Score"], colorscale="Viridis"),
            text=sector_stats["Conviction Score"].round(1),
            textposition="auto",
        )
    )

    fig.update_layout(
        title="Average Conviction Score by Sector",
        xaxis_title="Sector",
        yaxis_title="Avg Score",
        template="plotly_dark",
        height=500,
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        sector_stats.style.format(
            {"Conviction Score": "{:.1f}", "Consensus Ratio": "{:.2%}"}
        )
    )


def generate_pdf_report(df):
    """Generates a PDF report for top 5 stocks."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Analyst Conviction Report", ln=True, align="C")
    pdf.ln(10)

    top_5 = df.head(5)

    for i, row in top_5.iterrows():
        # Sanitize text for latin-1 encoding (fpdf limitation)
        def clean(text):
            return str(text).encode("latin-1", "replace").decode("latin-1")

        pdf.set_font("Arial", "B", 14)
        pdf.cell(
            200,
            10,
            txt=clean(f"{row['Rank']}. {row['Ticker']} - {row['Company Name']}"),
            ln=True,
        )

        pdf.set_font("Arial", size=12)
        pdf.cell(
            200,
            8,
            txt=clean(
                f"Price: ${row['Current Price']:.2f} | Score: {row['Conviction Score']:.1f}"
            ),
            ln=True,
        )
        pdf.cell(
            200,
            8,
            txt=clean(f"Sector: {row['Sector']} | Trend: {row['Trend']}"),
            ln=True,
        )
        pdf.cell(
            200,
            8,
            txt=clean(
                f"Analyst Rating: {row['Analyst Rating']} | Upside: {row['Implied Upside %']}"
            ),
            ln=True,
        )
        pdf.ln(5)

        # Note: Embedding dynamic plotly charts requires saving them as images first using kaleido.
        # For simplicity and reliability in this environment, we stick to text summary.
        # If kaleido is available, we could uncomment image generation logic.

        pdf.ln(5)

    return pdf.output(dest="S").encode("latin-1")


# --- Main App UI ---

st.title("📈 Analyst Conviction Dashboard")
st.markdown("""
This dashboard ranks stocks based on a **High Conviction Score**, blending **Fundamental Consensus** with **Technical Timing**.
""")

# Sidebar
st.sidebar.header("Controls")
if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Load Data
with st.spinner("Loading market data... This may take a few minutes on first run."):
    df = load_data()

if df is not None and not df.empty:
    # Save daily top picks for forward testing
    pm.save_daily_top_picks(df)

    # Sidebar Filters
    st.sidebar.header("Filters")

    sectors = sorted(df["Sector"].dropna().unique().tolist())
    selected_sectors = st.sidebar.multiselect("Select Sector", sectors, default=sectors)

    min_price = float(df["Current Price"].min())
    max_price = float(df["Current Price"].max())
    price_range = st.sidebar.slider(
        "Price Range ($)", min_price, max_price, (min_price, max_price)
    )

    min_analysts = st.sidebar.slider(
        "Min Analyst Count", 5, int(df["Total Analysts"].max()), 5
    )

    # Filter Data
    filtered_df = df[
        (df["Sector"].isin(selected_sectors))
        & (df["Current Price"] >= price_range[0])
        & (df["Current Price"] <= price_range[1])
        & (df["Total Analysts"] >= min_analysts)
    ]

    # Tabs
    tab1, tab2, tab3 = st.tabs(
        ["📊 Rankings & Deep Dive", "🌍 Market Overview", "💼 My Portfolio"]
    )

    with tab1:
        # Top Metrics
        st.subheader("🏆 Top High Conviction Picks")
        top_cols = st.columns(3)
        for i in range(3):
            if i < len(filtered_df):
                row = filtered_df.iloc[i]
                with top_cols[i]:
                    st.metric(
                        label=f"{row['Rank']}. {row['Ticker']}",
                        value=f"${row['Current Price']:.2f}",
                        delta=row["Implied Upside %"],
                    )
                    st.write(f"**Score:** {row['Conviction Score']:.1f}")
                    st.write(f"**Trend:** {row['Trend']}")

        # Main Table
        st.subheader("📊 Opportunity Rankings")

        display_cols = [
            "Rank",
            "Ticker",
            "Company Name",
            "Sector",
            "Conviction Score",
            "Current Price",
            "Implied Upside %",
            "Analyst Rating",
            "Total Analysts",
            "RSI",
            "Trend",
            "PEG Ratio",
            "News Sentiment",
            "News Risk",
        ]

        st.dataframe(
            filtered_df[display_cols],
            column_config={
                "Conviction Score": st.column_config.ProgressColumn(
                    "Score", format="%.1f", min_value=0, max_value=100
                ),
                "RSI": st.column_config.NumberColumn("RSI (14)", format="%.1f"),
                "PEG Ratio": st.column_config.NumberColumn("PEG", format="%.2f"),
                "News Sentiment": st.column_config.NumberColumn(
                    "News Sentiment",
                    format="%.2f",
                ),
            },
            use_container_width=True,
            height=400,
            selection_mode="single-row",
            on_select="ignore",
        )

        # Deep Dive Section
        st.markdown("---")
        st.subheader("🔍 Stock Deep Dive")

        col1, col2 = st.columns([1, 3])

        with col1:
            selected_ticker = st.selectbox(
                "Select Ticker for Analysis:", filtered_df["Ticker"].tolist()
            )

            if selected_ticker:
                # Buy Button Logic
                row = filtered_df[filtered_df["Ticker"] == selected_ticker].iloc[0]
                current_price = row["Current Price"]

                if st.button(f"💰 Buy $10,000 of {selected_ticker}"):
                    shares = 10000 / current_price
                    pm.add_trade(
                        selected_ticker, current_price, shares, row["Conviction Score"]
                    )
                    st.success(
                        f"Bought {shares:.2f} shares of {selected_ticker} at ${current_price:.2f}!"
                    )
                    st.balloons()

                # Show News
                st.write(f"**Latest News for {selected_ticker}**")
                try:
                    stock = yf.Ticker(selected_ticker)
                    news = stock.news
                    if news:
                        for item in news[:3]:
                            # Handle nested content structure
                            content = item.get("content", {})

                            # Title
                            title = item.get("title")
                            if not title:
                                title = content.get("title")

                            # Publisher
                            publisher = item.get("publisher")
                            if not publisher:
                                provider = content.get("provider", {})
                                publisher = provider.get("displayName", "Unknown")

                            # Date
                            pub_time = item.get("providerPublishTime")
                            date_str = "Unknown Date"
                            if pub_time:
                                date_str = pd.to_datetime(pub_time, unit="s").strftime(
                                    "%Y-%m-%d"
                                )
                            else:
                                pub_date_iso = content.get("pubDate")
                                if pub_date_iso:
                                    try:
                                        date_str = pd.to_datetime(
                                            pub_date_iso
                                        ).strftime("%Y-%m-%d")
                                    except:
                                        pass

                            # Link
                            link = item.get("link")
                            if not link:
                                link = content.get("canonicalUrl", {}).get("url")

                            with st.expander(f"{title if title else 'No Title'}"):
                                st.caption(f"{publisher} - {date_str}")
                                if link:
                                    st.markdown(f"[Read Full Story]({link})")
                                # Display sentiment for this headline if possible, but we only have aggregate.
                                # Re-calculating here for display would be nice but expensive?
                                # Let's just show the aggregate score for the stock above.

                        st.metric(
                            "Avg News Sentiment",
                            f"{row['News Sentiment']:.2f}",
                            delta=None,
                        )
                        if row["News Risk"]:
                            st.error(row["News Risk"])
                    else:
                        st.info("No recent news.")
                except Exception:
                    st.info("Could not fetch news.")

        with col2:
            if selected_ticker:
                plot_financial_chart(selected_ticker)

        # PDF Report
        st.markdown("---")
        if st.button("📄 Generate PDF Report (Top 5)"):
            pdf_bytes = generate_pdf_report(filtered_df)
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name="conviction_report.pdf",
                mime="application/pdf",
            )

    with tab2:
        st.subheader("🌍 Sector Strength Analysis")
        plot_sector_heatmap(filtered_df)

    with tab3:
        st.subheader("💼 Virtual Portfolio & Forward Testing")

        # Active Holdings
        st.markdown("### 🟢 Active Holdings")
        open_positions = pm.get_open_positions()

        if not open_positions.empty:
            # Fetch current prices for open positions
            # We can use the main 'df' if the ticker is there, otherwise fetch it.
            # For simplicity, let's assume most are in 'df' or fetch individually if needed.
            # To be robust, let's fetch current price for all open positions.

            total_invested = 0
            current_value = 0

            for index, trade in open_positions.iterrows():
                ticker = trade["ticker"]
                entry_price = trade["entry_price"]
                shares = trade["shares"]
                trade_id = trade["id"]

                # Get current price (Live Fetch for Real-Time P/L)
                try:
                    # Fetch live price to ensure P/L is accurate
                    ticker_info = yf.Ticker(ticker).info
                    current_price = ticker_info.get(
                        "currentPrice",
                        ticker_info.get("regularMarketPrice", entry_price),
                    )
                except Exception:
                    # Fallback to cached df if live fetch fails
                    current_price_row = df[df["Ticker"] == ticker]
                    if not current_price_row.empty:
                        current_price = current_price_row.iloc[0]["Current Price"]
                    else:
                        current_price = entry_price

                market_value = shares * current_price
                cost_basis = shares * entry_price
                unrealized_pl = market_value - cost_basis
                unrealized_pl_pct = (unrealized_pl / cost_basis) * 100

                total_invested += cost_basis
                current_value += market_value

                # UI Container for each holding
                with st.container(border=True):
                    cols = st.columns([4, 1])
                    with cols[0]:
                        st.markdown(
                            f"**{ticker}** | Shares: {shares:.2f} | Entry: ${entry_price:.2f} | Current: ${current_price:.2f}"
                        )
                        st.markdown(
                            f"P/L: :{'green' if unrealized_pl >= 0 else 'red'}[${unrealized_pl:.2f} ({unrealized_pl_pct:.2f}%)]"
                        )
                    with cols[1]:
                        if st.button("Sell", key=f"sell_{trade_id}"):
                            profit = pm.close_trade(trade_id, current_price)
                            st.success(f"Sold {ticker}! P/L: ${profit:.2f}")
                            if profit > 0:
                                st.balloons()
                            st.rerun()

            # Portfolio Metrics
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Invested", f"${total_invested:,.2f}")
            m2.metric(
                "Current Value",
                f"${current_value:,.2f}",
                delta=f"{current_value - total_invested:,.2f}",
            )
            total_return = (
                ((current_value - total_invested) / total_invested * 100)
                if total_invested > 0
                else 0
            )
            m3.metric("Total Return", f"{total_return:.2f}%")

        else:
            st.info("No active positions. Go to 'Rankings' and buy some stocks!")

        # Closed Trades History
        st.markdown("### 📜 Trade History")
        history = pm.get_portfolio_history()
        if not history.empty:
            st.dataframe(
                history[
                    [
                        "ticker",
                        "entry_date",
                        "exit_date",
                        "profit_loss",
                        "profit_loss_pct",
                        "entry_score",
                    ]
                ]
            )

            # Win/Loss Ratio
            wins = len(history[history["profit_loss"] > 0])
            losses = len(history[history["profit_loss"] <= 0])
            total = wins + losses
            if total > 0:
                st.metric(
                    "Win Rate", f"{(wins / total) * 100:.1f}%", f"{wins}W - {losses}L"
                )

            # Visual Validation
            st.markdown("### 📉 Conviction Score Validation")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=history["entry_score"],
                    y=history["profit_loss_pct"],
                    mode="markers",
                    text=history["ticker"],
                    marker=dict(
                        size=12,
                        color=history["profit_loss_pct"],
                        colorscale="RdYlGn",
                        showscale=True,
                    ),
                )
            )
            fig.update_layout(
                title="Entry Score vs. Realized Profit %",
                xaxis_title="Conviction Score at Entry",
                yaxis_title="Profit/Loss %",
                template="plotly_dark",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Watchlist History (Forward Testing)
        st.markdown("### 🔮 Forward Testing (Top 3 Daily Picks)")
        watchlist = pm.get_watchlist_history()
        if not watchlist.empty:
            st.dataframe(watchlist)
        else:
            st.info("No watchlist history yet. Check back tomorrow!")

        # Reset Button
        if st.button("⚠️ Reset Portfolio"):
            pm.reset_portfolio()
            st.warning("Portfolio reset!")
            st.rerun()

else:
    st.error("No data available. Please check your internet connection or try again.")
