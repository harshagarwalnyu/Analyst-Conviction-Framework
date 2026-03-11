from peewee import *
from datetime import datetime
import json
from src.core.models import TickerInfo, TradeRecord
from typing import List, Optional

db = SqliteDatabase("portfolio.db")


class BaseModel(Model):
    class Meta:
        database = db


class MarketData(BaseModel):
    ticker = CharField(primary_key=True)
    data_json = TextField()
    last_updated = DateTimeField(default=datetime.now)
    schema_version = IntegerField(default=1)  # To handle cache invalidation


class Trade(BaseModel):
    ticker = CharField()
    entry_price = FloatField()
    shares = FloatField()
    entry_date = DateTimeField(default=datetime.now)
    entry_score = FloatField()
    status = CharField(default="OPEN")  # 'OPEN' or 'CLOSED'
    exit_price = FloatField(null=True)
    exit_date = DateTimeField(null=True)
    profit_loss = FloatField(null=True)
    profit_loss_pct = FloatField(null=True)


class WatchlistHistory(BaseModel):
    date = DateField(default=datetime.now)
    ticker = CharField()
    rank = IntegerField()
    price = FloatField()
    score = FloatField()


class PortfolioManager:
    def __init__(self):
        db.connect(reuse_if_open=True)
        db.create_tables([MarketData, Trade, WatchlistHistory])

    def add_trade(self, ticker: str, price: float, shares: float, score: float):
        Trade.create(
            ticker=ticker,
            entry_price=price,
            shares=shares,
            entry_score=score,
            entry_date=datetime.now(),
        )

    def close_trade(self, trade_id: int, exit_price: float) -> Optional[float]:
        try:
            trade = Trade.get_by_id(trade_id)
            if trade.status == "CLOSED":
                return None

            trade.exit_price = exit_price
            trade.exit_date = datetime.now()
            trade.profit_loss = (exit_price - trade.entry_price) * trade.shares
            trade.profit_loss_pct = (
                (exit_price - trade.entry_price) / trade.entry_price
            ) * 100
            trade.status = "CLOSED"
            trade.save()
            return trade.profit_loss
        except Trade.DoesNotExist:
            return None

    def get_open_positions(self) -> List[Trade]:
        return list(Trade.select().where(Trade.status == "OPEN"))

    def get_portfolio_history(self) -> List[Trade]:
        return list(Trade.select().where(Trade.status == "CLOSED"))

    def save_daily_top_picks(self, analyses: List):
        today = datetime.now().date()
        # Check if already saved
        if not WatchlistHistory.select().where(WatchlistHistory.date == today).exists():
            for i, analysis in enumerate(analyses[:3]):
                WatchlistHistory.create(
                    date=today,
                    ticker=analysis.ticker,
                    rank=i + 1,
                    price=analysis.raw_data.current_price,
                    score=analysis.conviction_score,
                )

    def get_watchlist_history(self) -> List[WatchlistHistory]:
        return list(WatchlistHistory.select().order_by(WatchlistHistory.date.desc()))

    def reset_portfolio(self):
        Trade.delete().execute()
        WatchlistHistory.delete().execute()

    # --- Market Data Cache ---

    def save_market_data(self, data_list: List[TickerInfo]):
        with db.atomic():
            for data in data_list:
                MarketData.insert(
                    ticker=data.ticker,
                    data_json=data.model_dump_json(),
                    last_updated=datetime.now(),
                    schema_version=1,
                ).on_conflict_replace().execute()

    def get_market_data(self, tickers: List[str]) -> List[TickerInfo]:
        results = MarketData.select().where(
            (MarketData.ticker << tickers) & (MarketData.schema_version == 1)
        )
        data_list = []
        for row in results:
            try:
                data_list.append(TickerInfo.model_validate_json(row.data_json))
            except:
                pass
        return data_list

    def get_stale_tickers(
        self, tickers: List[str], ttl_minutes: int = 720
    ) -> List[str]:
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(minutes=ttl_minutes)

        # Tickers that are either missing OR older than cutoff OR wrong schema
        existing = MarketData.select(MarketData.ticker).where(
            (MarketData.ticker << tickers)
            & (MarketData.last_updated >= cutoff)
            & (MarketData.schema_version == 1)
        )
        existing_tickers = {row.ticker for row in existing}
        return [t for t in tickers if t not in existing_tickers]
