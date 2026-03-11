from fastapi import APIRouter, HTTPException
from schemas import BacktestRequest
from typing import Dict, Any
from src.core.backtest import BacktestEngine

router = APIRouter()


def get_backtest_engine():
    return BacktestEngine()


@router.post("/", response_model=Dict[str, Any])
def run_backtest(req: BacktestRequest):
    try:
        engine = get_backtest_engine()
        # For MVP we just backtest on a few top tickers to save time instead of all
        test_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
        result = engine.run_backtest(tickers=test_tickers, months_ago=req.months)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        # Adding some requested response structure if needed
        return {"status": "success", "backtest_data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
