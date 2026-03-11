import yfinance as yf
import pandas as pd
import requests
import time
import random
import logging
import numpy as np
from datetime import datetime
from io import StringIO
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from typing import List, Optional, Dict
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from src.core.models import TickerInfo

logger = logging.getLogger(__name__)


class DataFetcher:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def get_sp500_tickers(self) -> List[str]:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        return self._fetch_wiki_tickers(url, "Symbol")

    def get_sp400_tickers(self) -> List[str]:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies"
        # S&P 400 uses 'Symbol' or 'Ticker symbol'
        return self._fetch_wiki_tickers(
            url, ["Symbol", "Ticker symbol", "Ticker Symbol"]
        )

    def _fetch_wiki_tickers(self, url: str, col_names) -> List[str]:
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            tables = pd.read_html(StringIO(response.text))

            if isinstance(col_names, str):
                col_names = [col_names]

            df = None
            for table in tables:
                found_col = next((c for c in col_names if c in table.columns), None)
                if found_col:
                    df = table
                    target_col = found_col
                    break

            if df is None:
                return []

            tickers = df[target_col].tolist()
            return [str(t).replace(".", "-") for t in tickers]
        except Exception as e:
            logger.error(f"Error fetching tickers from {url}: {e}")
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def fetch_historical_state(
        self, ticker: str, months_ago: int = 1
    ) -> Optional[TickerInfo]:
        """Fetches the state of a ticker as it was N months ago."""
        try:
            ticker = ticker.replace(".", "-")
            stock = yf.Ticker(ticker)

            # 1. Recommendations at that time
            rec_summary = stock.get_recommendations_summary()
            if rec_summary is None or rec_summary.empty:
                return None

            period_str = f"-{months_ago}m" if months_ago > 0 else "0m"
            hist_rec = rec_summary[rec_summary["period"] == period_str]
            if hist_rec.empty:
                # Try fallback by index if period column is different
                if months_ago < len(rec_summary):
                    hist_rec = rec_summary.iloc[months_ago]
                else:
                    return None
            else:
                hist_rec = hist_rec.iloc[0]

            # 2. Historical Prices (History up to that point)
            # We need data up to 'months_ago' to calculate SMA/RSI as they were then.
            end_date = datetime.now() - pd.DateOffset(months=months_ago)
            start_date = end_date - pd.DateOffset(years=1)

            hist = stock.history(start=start_date, end=end_date + pd.Timedelta(days=1))
            if hist.empty or len(hist) < 20:
                return None

            current_price_then = float(hist["Close"].iloc[-1])

            # Technical Indicators at that time
            import pandas_ta as ta

            hist.ta.rsi(append=True)
            hist.ta.sma(length=50, append=True)
            hist.ta.sma(length=200, append=True)

            rsi = float(hist["RSI_14"].iloc[-1]) if "RSI_14" in hist.columns else None
            sma_50 = (
                float(hist["SMA_50"].iloc[-1]) if "SMA_50" in hist.columns else None
            )
            sma_200 = (
                float(hist["SMA_200"].iloc[-1]) if "SMA_200" in hist.columns else None
            )

            # Info (Note: yfinance .info is always current. We use proxies for historical info)
            # We'll use current sector/industry/name as they rarely change.
            # Price Target is hard to get historically via yfinance, so we'll use current target
            # as a conservative proxy or skip the 'upside' component for strict backtesting.
            # For this MVP, we use current target mean.
            info = stock.info

            return TickerInfo(
                ticker=ticker,
                name=info.get("longName", ticker),
                sector=info.get("sector", "Unknown"),
                industry=info.get("industry", "Unknown"),
                current_price=current_price_then,
                target_mean=info.get("targetMeanPrice", 0.0),  # Proxy
                peg_ratio=info.get("pegRatio"),
                beta=info.get("beta"),
                strong_buy=int(hist_rec.get("strongBuy", 0)),
                buy=int(hist_rec.get("buy", 0)),
                hold=int(hist_rec.get("hold", 0)),
                sell=int(hist_rec.get("sell", 0)),
                strong_sell=int(hist_rec.get("strongSell", 0)),
                total_analysts=int(
                    hist_rec.get("strongBuy", 0)
                    + hist_rec.get("buy", 0)
                    + hist_rec.get("hold", 0)
                    + hist_rec.get("sell", 0)
                    + hist_rec.get("strongSell", 0)
                ),
                rsi=rsi,
                sma_50=sma_50,
                sma_200=sma_200,
                avg_sentiment=0.0,  # Historical sentiment is expensive/hard to get
            )
        except Exception:
            return None

        """Fetches comprehensive data for a single ticker."""
        try:
            ticker = ticker.replace(".", "-")
            stock = yf.Ticker(ticker)

            # 1. Info & Recommendations
            info = stock.info
            if (
                not info
                or "currentPrice" not in info
                and "regularMarketPrice" not in info
            ):
                return None

            rec_summary = stock.get_recommendations_summary()

            strong_buy, buy, hold, sell, strong_sell = 0, 0, 0, 0, 0
            total_analysts = info.get("numberOfAnalystOpinions", 0) or 0

            if rec_summary is not None and not rec_summary.empty:
                latest_rec = rec_summary[rec_summary["period"] == "0m"]
                if latest_rec.empty:
                    latest_rec = rec_summary.iloc[0:1]
                else:
                    latest_rec = latest_rec.iloc[0:1]

                strong_buy = latest_rec.get("strongBuy", pd.Series([0])).iloc[0]
                buy = latest_rec.get("buy", pd.Series([0])).iloc[0]
                hold = latest_rec.get("hold", pd.Series([0])).iloc[0]
                sell = latest_rec.get("sell", pd.Series([0])).iloc[0]
                strong_sell = latest_rec.get("strongSell", pd.Series([0])).iloc[0]
                total_analysts = strong_buy + buy + hold + sell + strong_sell

            # 2. News Sentiment
            avg_sentiment = 0.0
            try:
                news = stock.news
                if news:
                    sentiments = []
                    for item in news[:10]:
                        title = item.get("title") or item.get("content", {}).get(
                            "title"
                        )
                        if title:
                            sentiments.append(
                                self.sia.polarity_scores(title)["compound"]
                            )
                    if sentiments:
                        avg_sentiment = float(np.mean(sentiments))
            except Exception:
                pass

            # 3. Technical Indicators (1 Year History)
            hist = stock.history(period="1y")
            rsi, sma_50, sma_200 = None, None, None

            if not hist.empty and len(hist) >= 14:
                import pandas_ta as ta

                hist.ta.rsi(append=True)
                hist.ta.sma(length=50, append=True)
                hist.ta.sma(length=200, append=True)

                rsi = (
                    float(hist["RSI_14"].iloc[-1]) if "RSI_14" in hist.columns else None
                )
                sma_50 = (
                    float(hist["SMA_50"].iloc[-1]) if "SMA_50" in hist.columns else None
                )
                sma_200 = (
                    float(hist["SMA_200"].iloc[-1])
                    if "SMA_200" in hist.columns
                    else None
                )

            return TickerInfo(
                ticker=ticker,
                name=info.get("longName", ticker),
                sector=info.get("sector", "Unknown"),
                industry=info.get("industry", "Unknown"),
                current_price=info.get(
                    "currentPrice", info.get("regularMarketPrice", 0.0)
                ),
                target_mean=info.get("targetMeanPrice", 0.0),
                peg_ratio=info.get("pegRatio"),
                beta=info.get("beta"),
                strong_buy=int(strong_buy),
                buy=int(buy),
                hold=int(hold),
                sell=int(sell),
                strong_sell=int(strong_sell),
                total_analysts=int(total_analysts),
                rsi=rsi,
                sma_50=sma_50,
                sma_200=sma_200,
                avg_sentiment=avg_sentiment,
            )
        except Exception as e:
            if "404" in str(e):
                return None
            raise e
