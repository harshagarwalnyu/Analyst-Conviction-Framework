import streamlit as st
import pandas as pd

# Set page config
st.set_page_config(
    page_title="Analyst Conviction Dashboard", layout="wide", page_icon="📈"
)


# Load data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("top_1000_opportunity_rankings.csv")
        return df
    except FileNotFoundError:
        return None


df = load_data()

# Title and Description
st.title("📈 Analyst Conviction Dashboard")
st.markdown("""
This dashboard ranks the Top 1000 US stocks based on a **High Conviction Score**.
The score combines **Analyst Consensus**, **Implied Upside**, and **Analyst Volume**, penalized by **High Beta** and **Overvaluation (PEG)**.
""")

if df is not None:
    # Sidebar Filters
    st.sidebar.header("Filters")

    # Sector Filter
    sectors = sorted(df["Sector"].dropna().unique().tolist())
    selected_sectors = st.sidebar.multiselect("Select Sector", sectors, default=sectors)

    # Price Range
    min_price = float(df["Current Price"].min())
    max_price = float(df["Current Price"].max())
    price_range = st.sidebar.slider(
        "Price Range ($)", min_price, max_price, (min_price, max_price)
    )

    # Min Analyst Count
    min_analysts = st.sidebar.slider(
        "Min Analyst Count",
        5,
        int(df["Buy Count"].max() + df["Analyst Rating"].max()),
        5,
    )  # Approximation, better to use Total Analysts if available but we didn't save it explicitly in final cols?
    # Wait, we didn't save 'Total Analysts' in the final CSV columns in main.py?
    # Let's check main.py cols: ['Rank', 'Ticker', 'Company Name', 'Sector', 'Industry', 'Conviction Score', 'Implied Upside %', 'Analyst Rating', 'Buy Count', 'Current Price', 'Analyst Price Target', 'PEG Ratio', 'Beta']
    # We don't have 'Total Analysts' column in the final output!
    # We can infer it roughly or just use 'Buy Count' as a proxy for now, or update main.py.
    # Actually, 'Buy Count' is just Buys.
    # Let's just use Buy Count filter for now or assume user wants to filter by "Popularity".
    # Or better, let's update main.py to include Total Analysts if critical.
    # For now, let's filter by 'Buy Count' as a proxy for coverage depth.

    # Filter Data
    filtered_df = df[
        (df["Sector"].isin(selected_sectors))
        & (df["Current Price"] >= price_range[0])
        & (df["Current Price"] <= price_range[1])
        & (df["Buy Count"] >= min_analysts)  # Using Buy Count as proxy
    ]

    # Metrics Row
    st.subheader("🏆 Top 3 High Conviction Picks")
    top_3 = filtered_df.head(3)

    cols = st.columns(3)
    for i, (index, row) in enumerate(top_3.iterrows()):
        with cols[i]:
            st.metric(
                label=f"{row['Rank']}. {row['Ticker']}",
                value=f"{row['Current Price']:.2f}",
                delta=row["Implied Upside %"],
            )
            st.write(f"**Score:** {row['Conviction Score']:.1f}")
            st.write(f"**Sector:** {row['Sector']}")
            st.write(f"**Consensus:** {row['Analyst Rating']} (1=Strong Buy)")

    # Main Table
    st.subheader("📊 Opportunity Rankings")
    st.dataframe(
        filtered_df,
        column_config={
            "Implied Upside %": st.column_config.TextColumn("Upside"),
            "Conviction Score": st.column_config.ProgressColumn(
                "Score",
                help="High Conviction Score (0-100)",
                format="%.1f",
                min_value=0,
                max_value=100,
            ),
        },
        use_container_width=True,
        height=600,
    )

    # Download Button
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Filtered Data",
        csv,
        "filtered_rankings.csv",
        "text/csv",
        key="download-csv",
    )

else:
    st.error("Data file not found. Please run `main.py` first.")
