from fastapi import APIRouter, HTTPException, Depends
from typing import List
from schemas import TradeRecordSchema, PortfolioActionRequest, PortfolioSellRequest
from src.database.portfolio import PortfolioManager

router = APIRouter()


def get_portfolio_manager():
    return PortfolioManager()


@router.get("/", response_model=List[TradeRecordSchema])
def get_portfolio(pm: PortfolioManager = Depends(get_portfolio_manager)):
    try:
        trades = pm.get_open_positions()
        # Convert peewee models to schemas
        return [
            {
                "id": t.id,
                "ticker": t.ticker,
                "entry_price": t.entry_price,
                "shares": t.shares,
                "entry_date": t.entry_date,
                "entry_score": t.entry_score,
                "status": t.status,
                "exit_price": t.exit_price,
                "exit_date": t.exit_date,
                "profit_loss": t.profit_loss,
                "profit_loss_pct": t.profit_loss_pct,
            }
            for t in trades
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buy", response_model=dict)
def buy_stock(
    req: PortfolioActionRequest, pm: PortfolioManager = Depends(get_portfolio_manager)
):
    try:
        pm.add_trade(req.ticker, req.price, req.shares, req.score)
        return {
            "status": "success",
            "message": f"Bought {req.shares} shares of {req.ticker}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sell", response_model=dict)
def sell_stock(
    req: PortfolioSellRequest, pm: PortfolioManager = Depends(get_portfolio_manager)
):
    try:
        profit = pm.close_trade(req.trade_id, req.exit_price)
        if profit is None:
            raise HTTPException(
                status_code=400, detail="Trade could not be closed or already closed"
            )
        return {
            "status": "success",
            "message": f"Sold trade {req.trade_id}. Profit: {profit}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
