from fastapi import APIRouter, HTTPException
from typing import List
from schemas import NewsItem
import random
import time

router = APIRouter()


@router.get("/{symbol}", response_model=List[NewsItem])
def get_news(symbol: str):
    # Mock data bindings for MVP
    # In real implementation, this could fetch from yfinance or a news API
    publishers = ["Bloomberg", "Reuters", "CNBC", "Yahoo Finance"]
    return [
        NewsItem(
            title=f"Latest update on {symbol} market performance",
            publisher=random.choice(publishers),
            link=f"https://finance.yahoo.com/quote/{symbol}",
            providerPublishTime=int(time.time()) - random.randint(3600, 86400),
            relatedTickers=[symbol],
        ),
        NewsItem(
            title=f"{symbol} analysts upgrade price target",
            publisher=random.choice(publishers),
            link=f"https://finance.yahoo.com/quote/{symbol}",
            providerPublishTime=int(time.time()) - random.randint(86400, 172800),
            relatedTickers=[symbol],
        ),
    ]
