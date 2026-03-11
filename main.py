import sys
import subprocess
import argparse
from src.services.analysis_service import AnalysisService
from tabulate import tabulate


def run_dashboard():
    """Launch the Streamlit dashboard."""
    print("Launching Analyst Conviction Dashboard...")
    subprocess.run(["uv", "run", "streamlit", "run", "src/web/app.py"])


def run_cli_analysis(limit=20):
    """Run analysis and print to console."""
    service = AnalysisService()
    print(f"Running analysis for S&P 500 and S&P 400...")

    def progress(current, total):
        if current % 10 == 0:
            print(f"Progress: {current}/{total} tickers...")

    analyses = service.run_full_analysis(progress_callback=progress)

    if not analyses:
        print("No data collected.")
        return

    # Prepare table
    table_data = []
    for a in analyses[:limit]:
        table_data.append(
            [
                a.ticker,
                a.raw_data.name,
                a.conviction_score,
                a.implied_upside_pct,
                a.analyst_rating,
                a.trend,
            ]
        )

    headers = ["Ticker", "Company", "Score", "Upside", "Rating", "Trend"]
    print("\nTop High Conviction Stocks:")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stock Market Analyst Conviction Tool")
    parser.add_argument(
        "--cli", action="store_true", help="Run in CLI mode instead of dashboard"
    )
    parser.add_argument(
        "--limit", type=int, default=20, help="Number of results to show in CLI mode"
    )

    args = parser.parse_args()

    if args.cli:
        run_cli_analysis(limit=args.limit)
    else:
        run_dashboard()
