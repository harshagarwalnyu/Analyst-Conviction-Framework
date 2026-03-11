from fastapi import APIRouter, HTTPException, Depends
from schemas import TickerInfoSchema
from src.services.analysis_service import AnalysisService

router = APIRouter()


def get_analysis_service():
    return AnalysisService()


@router.get("/{symbol}", response_model=TickerInfoSchema)
def get_ticker(symbol: str, service: AnalysisService = Depends(get_analysis_service)):
    info = service.get_ticker_deep_dive(symbol)
    if not info:
        raise HTTPException(
            status_code=404, detail="Ticker not found or data unavailable"
        )
    return info
