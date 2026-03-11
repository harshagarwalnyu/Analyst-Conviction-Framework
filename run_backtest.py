from src.core.backtest import BacktestEngine
from src.api.data_fetcher import DataFetcher
import json


def main():
    fetcher = DataFetcher()
    engine = BacktestEngine()

    # Get a small sample of tickers
    print("Fetching tickers...")
    tickers = fetcher.get_sp500_tickers()[:30]  # Test with 30 tickers

    print(f"Running backtest for {len(tickers)} tickers...")

    # Debug individual fetches
    for t in tickers[:5]:
        res = fetcher.fetch_historical_state(t, months_ago=2)
        if res:
            print(
                f"DEBUG: Found historical state for {t}: Price {res.current_price}, Analysts {res.total_analysts}"
            )
        else:
            print(f"DEBUG: Failed to find historical state for {t}")

    summary = engine.run_backtest(tickers, months_ago=2)

    print("\n=== Backtest Summary (2 Months) ===")
    print(f"SPY Return: {summary.get('spy_return', 0) * 100:.2f}%")
    print(
        f"High Conviction Avg Return: {summary.get('high_conviction_avg_return', 0) * 100:.2f}%"
    )
    print(
        f"Mid Conviction Avg Return: {summary.get('mid_conviction_avg_return', 0) * 100:.2f}%"
    )
    print(
        f"Low Conviction Avg Return: {summary.get('low_conviction_avg_return', 0) * 100:.2f}%"
    )
    print(f"Win Rate vs SPY: {summary.get('win_rate_vs_spy', 0) * 100:.1f}%")
    print(f"High Conviction Count: {summary.get('high_conviction_count', 0)}")

    from tabulate import tabulate

    print("\n=== Full Backtest Results (Sorted by Score) ===")
    table_data = []
    for r in summary.get("all_results", []):
        table_data.append(
            [
                r["ticker"],
                r["score"],
                f"{r['return'] * 100:.2f}%",
                "✅" if r["return"] > summary["spy_return"] else "❌",
            ]
        )

    headers = ["Ticker", "Score", "Return", "Beat SPY?"]
    print(tabulate(table_data, headers=headers, tablefmt="psql"))


if __name__ == "__main__":
    main()
