import concurrent.futures
from typing import List, Dict, Optional
import pandas as pd
from src.api.data_fetcher import DataFetcher
from src.core.scoring import ScoringEngine
from src.database.portfolio import PortfolioManager
from src.core.models import ConvictionAnalysis, TickerInfo
import logging

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self):
        self.fetcher = DataFetcher()
        self.pm = PortfolioManager()
        self.engine = ScoringEngine()

    def get_all_tickers(self) -> List[str]:
        sp500 = self.fetcher.get_sp500_tickers()
        sp400 = self.fetcher.get_sp400_tickers()
        return list(set(sp500 + sp400))

    def run_full_analysis(self, progress_callback=None) -> List[ConvictionAnalysis]:
        tickers = self.get_all_tickers()
        if not tickers:
            return []

        # 1. Cache Check
        stale_tickers = self.pm.get_stale_tickers(tickers)
        fresh_tickers = [t for t in tickers if t not in stale_tickers]

        all_ticker_data = []

        # Load from cache
        if fresh_tickers:
            all_ticker_data.extend(self.pm.get_market_data(fresh_tickers))

        # 2. Fetch Stale Data
        if stale_tickers:
            fetched_data = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(self.fetcher.fetch_ticker_data, t): t
                    for t in stale_tickers
                }

                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    ticker = futures[future]
                    try:
                        data = future.result()
                        if data:
                            fetched_data.append(data)
                            all_ticker_data.append(data)
                    except Exception as e:
                        logger.error(f"Failed to fetch {ticker}: {e}")

                    completed += 1
                    if progress_callback:
                        progress_callback(completed, len(stale_tickers))

            # Save to cache
            if fetched_data:
                self.pm.save_market_data(fetched_data)

        # 3. Score
        analyses = self.engine.batch_calculate(all_ticker_data)

        # Sort by score
        analyses.sort(key=lambda x: x.conviction_score, reverse=True)

        # Save top picks for tracking
        self.pm.save_daily_top_picks(analyses)

        return analyses

    def get_ticker_deep_dive(self, ticker: str) -> Optional[TickerInfo]:
        """Fetch real-time data for a single ticker."""
        return self.fetcher.fetch_ticker_data(ticker)
