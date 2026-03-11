import pandas as pd
import numpy as np
from typing import List, Optional
from src.core.models import TickerInfo, ConvictionAnalysis


class ScoringEngine:
    @staticmethod
    def calculate_conviction_score(
        data: TickerInfo, max_analysts: int = 40
    ) -> ConvictionAnalysis:
        """Calculates the Conviction Score for a single ticker."""

        # 1. Analyst Consensus (30% - Rebalanced from 40%)
        consensus_ratio = (
            (data.strong_buy + data.buy) / data.total_analysts
            if data.total_analysts >= 5
            else 0
        )
        score_consensus = consensus_ratio * 30

        # 2. Implied Upside (30% - Rebalanced from 40%)
        implied_upside_raw = (
            ((data.target_mean - data.current_price) / data.current_price)
            if data.current_price > 0
            else 0
        )
        score_upside = min(max(implied_upside_raw, 0), 0.5) / 0.5 * 30

        # 3. Analyst Volume (20%)
        score_volume = (
            (data.total_analysts / max_analysts) * 20 if max_analysts > 0 else 0
        )
        score_volume = min(score_volume, 20)

        # 4. Trend & Momentum (20% - New Component)
        score_trend = 0
        trend_status = "N/A"
        if data.sma_200 and data.current_price:
            if data.current_price > data.sma_200:
                score_trend += 10  # Long term uptrend
                trend_status = "Uptrend 🟢"
            else:
                score_trend -= 20  # Severe penalty for falling knife
                trend_status = "Downtrend 🔴"

        if data.sma_50 and data.sma_200:
            if data.sma_50 > data.sma_200:
                score_trend += 10  # Golden Cross
            else:
                score_trend -= 5  # Death Cross

        # 5. Penalties & Boosts
        penalty_beta = 10 if (data.beta and data.beta > 1.5) else 0

        penalty_peg = 0
        if data.peg_ratio is not None:
            if data.peg_ratio > 2.5:
                penalty_peg = 15
            elif data.peg_ratio < 0:
                penalty_peg = 10

        # News Sentiment Modifier
        score_sentiment = 0
        if data.avg_sentiment < -0.1:
            score_sentiment = -20
        elif data.avg_sentiment > 0.1:
            score_sentiment = 10

        news_risk = "⚠️ NEWS RISK" if data.avg_sentiment < -0.5 else ""

        # TA Modifiers
        score_ta = 0
        if data.rsi is not None:
            if data.rsi > 70:
                score_ta -= 15  # Stricter overbought
            elif 35 <= data.rsi <= 45 and consensus_ratio >= 0.8:
                score_ta += 15  # Stricter dip buying

        # Total Score
        conviction_score = (
            score_consensus
            + score_upside
            + score_volume
            + score_trend
            - penalty_beta
            - penalty_peg
            + score_ta
            + score_sentiment
        )

        conviction_score = max(0, min(100, conviction_score))

        # Extra Formatting
        upside_fmt = (
            f"+{implied_upside_raw * 100:.1f}%"
            if implied_upside_raw > 0
            else f"{implied_upside_raw * 100:.1f}%"
        )

        # Analyst Rating (1-5)
        analyst_rating = 0
        if data.total_analysts > 0:
            analyst_rating = (
                data.strong_buy * 1
                + data.buy * 2
                + data.hold * 3
                + data.sell * 4
                + data.strong_sell * 5
            ) / data.total_analysts

        return ConvictionAnalysis(
            ticker=data.ticker,
            conviction_score=round(conviction_score, 1),
            consensus_ratio=round(consensus_ratio, 3),
            implied_upside_pct=upside_fmt,
            analyst_rating=round(analyst_rating, 2),
            trend=trend_status,
            news_risk=news_risk,
            score_breakdown={
                "consensus": score_consensus,
                "upside": score_upside,
                "volume": score_volume,
                "trend": score_trend,
                "beta_penalty": -penalty_beta,
                "peg_penalty": -penalty_peg,
                "ta_modifier": score_ta,
                "sentiment": score_sentiment,
            },
            raw_data=data,
        )

    @classmethod
    def batch_calculate(
        cls, ticker_data_list: List[TickerInfo]
    ) -> List[ConvictionAnalysis]:
        """Calculates scores for a list of tickers, handling global max_analysts."""
        if not ticker_data_list:
            return []

        max_analysts = (
            max([d.total_analysts for d in ticker_data_list])
            if ticker_data_list
            else 40
        )
        return [
            cls.calculate_conviction_score(d, max_analysts)
            for d in ticker_data_list
            if d.total_analysts >= 5
        ]
