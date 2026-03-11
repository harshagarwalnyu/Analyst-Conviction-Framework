import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import pandas_ta as ta
from src.services.analysis_service import AnalysisService
from src.database.portfolio import PortfolioManager
from datetime import datetime
import os
import nltk

# Initialize
service = AnalysisService()
pm = PortfolioManager()

# nltk check
try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon")

# Page Config
st.set_page_config(
    page_title="Analyst Conviction Dashboard", layout="wide", page_icon="📈"
)

# --- UI Components ---


def plot_chart(ticker: str):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y")
    if hist.empty:
        return

    hist.ta.rsi(append=True)
    hist.ta.sma(length=50, append=True)
    hist.ta.sma(length=200, append=True)

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3]
    )

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

    if "SMA_50" in hist.columns:
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
    if "SMA_200" in hist.columns:
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
    if "RSI_14" in hist.columns:
        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist["RSI_14"],
                line=dict(color="purple", width=1.5),
                name="RSI",
            ),
            row=2,
            col=1,
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    fig.update_layout(
        height=500,
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


# --- App Layout ---

st.title("📈 Analyst Conviction Dashboard")
st.markdown("---")


# Data Loading
@st.cache_data(ttl=3600 * 12)
def load_cached_analysis():
    progress_bar = st.progress(0)
    status_text = st.empty()

    def on_progress(current, total):
        progress_bar.progress(current / total)
        status_text.text(f"Updating data: {current}/{total} tickers processed...")

    data = service.run_full_analysis(progress_callback=on_progress)
    progress_bar.empty()
    status_text.empty()
    return data


# Refresh Logic
if st.sidebar.button("🔄 Full Data Refresh"):
    st.cache_data.clear()
    st.rerun()

analyses = load_cached_analysis()

if not analyses:
    st.error("No data found. Please check your connection.")
    st.stop()

# Convert to DF for filtering
rows = []
for a in analyses:
    rows.append(
        {
            "Ticker": a.ticker,
            "Name": a.raw_data.name,
            "Sector": a.raw_data.sector,
            "Score": a.conviction_score,
            "Price": a.raw_data.current_price,
            "Upside": a.implied_upside_pct,
            "Rating": a.analyst_rating,
            "Analysts": a.raw_data.total_analysts,
            "Trend": a.trend,
            "RSI": a.raw_data.rsi,
            "PEG": a.raw_data.peg_ratio,
            "Sentiment": a.raw_data.avg_sentiment,
            "Risk": a.news_risk,
            "Object": a,  # Pass the full object for deep dive
        }
    )
df = pd.DataFrame(rows)

# Sidebar Filters
st.sidebar.header("Filters")
selected_sectors = st.sidebar.multiselect(
    "Sectors",
    sorted(df["Sector"].unique().tolist()),
    default=df["Sector"].unique().tolist(),
)
min_score = st.sidebar.slider("Min Score", 0, 100, 70)
min_analysts = st.sidebar.slider("Min Analysts", 5, 40, 10)

filtered_df = df[
    (df["Sector"].isin(selected_sectors))
    & (df["Score"] >= min_score)
    & (df["Analysts"] >= min_analysts)
]

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Rankings", "🌍 Market Map", "💼 Portfolio"])

with tab1:
    st.subheader("Top High Conviction Picks")
    cols = st.columns(3)
    for i in range(min(3, len(filtered_df))):
        row = filtered_df.iloc[i]
        with cols[i]:
            st.metric(f"{row['Ticker']}", f"${row['Price']:.2f}", delta=row["Upside"])
            st.write(f"**Score: {row['Score']}** | {row['Trend']}")

    st.markdown("---")
    st.dataframe(
        filtered_df.drop(columns=["Object"]),
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Score", min_value=0, max_value=100
            ),
            "Sentiment": st.column_config.NumberColumn("Sentiment", format="%.2f"),
        },
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.subheader("🔍 Stock Deep Dive")
    selected_ticker = st.selectbox(
        "Select for analysis", filtered_df["Ticker"].tolist()
    )

    if selected_ticker:
        analysis = filtered_df[filtered_df["Ticker"] == selected_ticker].iloc[0][
            "Object"
        ]
        d1, d2 = st.columns([1, 2])
        with d1:
            st.write(f"### {analysis.raw_data.name}")
            st.write(f"**Sector:** {analysis.raw_data.sector}")
            st.write(
                f"**Analysts:** {analysis.raw_data.total_analysts} (Rating: {analysis.analyst_rating})"
            )
            st.write(f"**Upside:** {analysis.implied_upside_pct}")
            st.write(f"**Conviction Score: {analysis.conviction_score}**")

            if st.button(f"Buy 10k of {selected_ticker}"):
                pm.add_trade(
                    selected_ticker,
                    analysis.raw_data.current_price,
                    10000 / analysis.raw_data.current_price,
                    analysis.conviction_score,
                )
                st.success("Trade added!")
                st.rerun()

            st.write("#### Score Breakdown")
            st.json(analysis.score_breakdown)

        with d2:
            plot_chart(selected_ticker)

with tab2:
    st.subheader("Sector Performance")
    sector_stats = (
        df.groupby("Sector")["Score"].mean().sort_values(ascending=False).reset_index()
    )
    fig = go.Figure(
        go.Bar(x=sector_stats["Sector"], y=sector_stats["Score"], marker_color="indigo")
    )
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Portfolio Manager")
    open_trades = pm.get_open_positions()
    if open_trades:
        for t in open_trades:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.write(
                    f"**{t.ticker}** | Entry: ${t.entry_price:.2f} | Score: {t.entry_score}"
                )
                if c2.button("Sell", key=f"sell_{t.id}"):
                    # In a real app, fetch current price. For now, use entry or a fallback.
                    live_price = yf.Ticker(t.ticker).info.get(
                        "currentPrice", t.entry_price
                    )
                    pm.close_trade(t.id, live_price)
                    st.success("Sold!")
                    st.rerun()
    else:
        st.info("No open positions.")

    st.markdown("---")
    history = pm.get_portfolio_history()
    if history:
        st.write("### Closed Trades")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Ticker": h.ticker,
                        "Profit": h.profit_loss,
                        "P/L %": h.profit_loss_pct,
                        "Entry": h.entry_date.strftime("%Y-%m-%d"),
                        "Exit": h.exit_date.strftime("%Y-%m-%d"),
                    }
                    for h in history
                ]
            )
        )

        if st.button("Reset All Data"):
            pm.reset_portfolio()
            st.rerun()
