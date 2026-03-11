from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import asyncio
import json
import random
from typing import List

router = APIRouter()


async def price_generator(symbols: List[str]):
    while True:
        # Mock price stream for MVP
        for symbol in symbols:
            # Generate a random mock price change
            change = random.uniform(-0.5, 0.5)
            data = {
                "symbol": symbol,
                "price": round(100.0 + (random.random() * 50) + change, 2),
                "change": round(change, 2),
                "change_pct": round(change / 100, 4),
            }
            yield f"data: {json.dumps(data)}\n\n"
        await asyncio.sleep(2)


@router.get("/prices")
async def stream_prices(
    symbols: str = Query(..., description="Comma-separated list of symbols"),
):
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="No symbols provided")

    return StreamingResponse(
        price_generator(symbol_list), media_type="text/event-stream"
    )
