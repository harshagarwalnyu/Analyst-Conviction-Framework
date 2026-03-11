import concurrent.futures
from typing import List, Dict, Optional
import pandas as pd
import yfinance as yf
from src.api.data_fetcher import DataFetcher
from src.core.scoring import ScoringEngine
from src.core.models import ConvictionAnalysis, TickerInfo
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BacktestEngine:
    def __init__(self):
        self.fetcher = DataFetcher()
        self.engine = ScoringEngine()

    def run_backtest(self, tickers: List[str], months_ago: int = 2) -> Dict:
        """Runs a backtest on a list of tickers from N months ago."""
        print(
            f"Starting backtest for {len(tickers)} tickers from {months_ago} months ago..."
        )

        # 1. Fetch historical state and current price for all
        historical_data: List[TickerInfo] = []
        current_prices: Dict[str, float] = {}

        # Fetch SPY benchmark performance
        spy = yf.Ticker("SPY")
        period = f"{months_ago + 1}mo" if (months_ago + 1) <= 12 else "1y"
        spy_hist = spy.history(period=period)
        if len(spy_hist) < (months_ago * 20):
            spy_start_price = spy_hist["Close"].iloc[0]
        else:
            spy_start_price = spy_hist["Close"].iloc[-(months_ago * 21) - 1]
        spy_end_price = spy_hist["Close"].iloc[-1]
        spy_return = (spy_end_price - spy_start_price) / spy_start_price

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Task A: Fetch historical states
            hist_futures = {
                executor.submit(self.fetcher.fetch_historical_state, t, months_ago): t
                for t in tickers
            }
            # Task B: Fetch current prices
            curr_futures = {
                executor.submit(
                    lambda ticker: yf.Ticker(ticker).info.get("currentPrice"), t
                ): t
                for t in tickers
            }

            for future in concurrent.futures.as_completed(hist_futures):
                res = future.result()
                if res:
                    historical_data.append(res)

            for future in concurrent.futures.as_completed(curr_futures):
                ticker = curr_futures[future]
                try:
                    res = future.result()
                    if res:
                        current_prices[ticker] = res
                except:
                    pass

        # 2. Score historical data
        analyses = self.engine.batch_calculate(historical_data)

        # 3. Calculate returns
        results = []
        for a in analyses:
            if a.ticker in current_prices:
                start_price = a.raw_data.current_price
                end_price = current_prices[a.ticker]
                ret = (end_price - start_price) / start_price

                results.append(
                    {
                        "ticker": a.ticker,
                        "score": a.conviction_score,
                        "return": ret,
                        "upside_at_start": a.implied_upside_pct,
                        "rating_at_start": a.analyst_rating,
                    }
                )

        if not results:
            return {"error": "No results collected"}

        df = pd.DataFrame(results)

        # 4. Group by Score Tiers
        high_conviction = df[df["score"] >= 80]
        mid_conviction = df[(df["score"] >= 60) & (df["score"] < 80)]
        low_conviction = df[df["score"] < 60]

        summary = {
            "period_months": months_ago,
            "spy_return": spy_return,
            "high_conviction_avg_return": high_conviction["return"].mean()
            if not high_conviction.empty
            else 0,
            "mid_conviction_avg_return": mid_conviction["return"].mean()
            if not mid_conviction.empty
            else 0,
            "low_conviction_avg_return": low_conviction["return"].mean()
            if not low_conviction.empty
            else 0,
            "high_conviction_count": len(high_conviction),
            "total_count": len(df),
            "win_rate_vs_spy": (df["return"] > spy_return).mean()
            if not df.empty
            else 0,
            "top_performers": df.sort_values(by="return", ascending=False)
            .head(5)
            .to_dict("records"),
            "all_results": df.sort_values(by="score", ascending=False).to_dict(
                "records"
            ),
        }

        return summary
