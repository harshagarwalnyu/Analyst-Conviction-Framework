import pytest
from src.core.models import TickerInfo
from src.core.scoring import ScoringEngine


def test_conviction_score_high():
    """Test a stock with strong fundamentals and upside."""
    data = TickerInfo(
        ticker="AAPL",
        name="Apple Inc.",
        current_price=100.0,
        target_mean=150.0,  # 50% upside
        strong_buy=10,
        buy=10,
        total_analysts=20,  # 100% consensus
        rsi=40,  # Dip buying boost (+10)
        sma_200=90,  # Uptrend
        avg_sentiment=0.1,  # Positive sentiment (+5)
    )

    analysis = ScoringEngine.calculate_conviction_score(data)

    # Consensus: 1.0 * 40 = 40
    # Upside: 0.5 * 40 = 40
    # Volume: 20/40 * 20 = 10
    # TA: +10 (RSI 40 + High Consensus)
    # Sentiment: +5
    # Total = 40 + 40 + 10 + 10 + 5 = 105 -> clipped to 100

    assert analysis.conviction_score == 100.0
    assert analysis.trend == "Uptrend 🟢"
    assert analysis.score_breakdown["consensus"] == 40.0
    assert analysis.score_breakdown["upside"] == 40.0


def test_conviction_score_penalties():
    """Test a stock with low analysts and high beta/peg."""
    data = TickerInfo(
        ticker="SPEC",
        name="Speculative Co",
        current_price=100.0,
        target_mean=100.0,  # 0% upside
        strong_buy=0,
        buy=1,
        total_analysts=5,  # 20% consensus
        beta=2.5,  # -10 penalty
        peg_ratio=4.0,  # -10 penalty
        rsi=80,  # -10 penalty
        avg_sentiment=-0.1,  # -15 penalty
    )

    analysis = ScoringEngine.calculate_conviction_score(data)

    # Consensus: 0.2 * 40 = 8
    # Upside: 0
    # Volume: 5/40 * 20 = 2.5
    # Beta Penalty: -10
    # PEG Penalty: -10
    # TA Penalty: -10
    # Sentiment Penalty: -15
    # Total = 8 + 0 + 2.5 - 10 - 10 - 10 - 15 = -24.5 -> clipped to 0

    assert analysis.conviction_score == 0.0
    assert analysis.score_breakdown["beta_penalty"] == -10
