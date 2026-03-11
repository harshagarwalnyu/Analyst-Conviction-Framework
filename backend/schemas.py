from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class TickerInfoSchema(BaseModel):
    ticker: str
    name: str
    sector: str = "Unknown"
    industry: str = "Unknown"
    current_price: float
    target_mean: float = 0.0
    peg_ratio: Optional[float] = None
    beta: Optional[float] = None
    strong_buy: int = 0
    buy: int = 0
    hold: int = 0
    sell: int = 0
    strong_sell: int = 0
    total_analysts: int = 0
    rsi: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    avg_sentiment: float = 0.0


class RankingSchema(BaseModel):
    ticker: str
    conviction_score: float
    consensus_ratio: float
    implied_upside_pct: str
    analyst_rating: float
    trend: str
    news_risk: str
    score_breakdown: Dict[str, float]
    raw_data: TickerInfoSchema
    last_updated: datetime


class TradeRecordSchema(BaseModel):
    id: Optional[int] = None
    ticker: str
    entry_price: float
    shares: float
    entry_date: datetime
    entry_score: float
    status: str
    exit_price: Optional[float] = None
    exit_date: Optional[datetime] = None
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None


class PortfolioActionRequest(BaseModel):
    ticker: str
    price: float
    shares: float
    score: float = 0.0


class PortfolioSellRequest(BaseModel):
    trade_id: int
    exit_price: float


class BacktestRequest(BaseModel):
    initial_capital: float = 100000.0
    months: int = 6


class BacktestResult(BaseModel):
    final_value: float
    total_return_pct: float
    benchmark_return_pct: float
    win_rate: float
    trades_executed: int


class SectorSchema(BaseModel):
    sector: str
    avg_score: float
    ticker_count: int


class NewsItem(BaseModel):
    title: str
    publisher: str
    link: str
    providerPublishTime: int
    relatedTickers: List[str]
