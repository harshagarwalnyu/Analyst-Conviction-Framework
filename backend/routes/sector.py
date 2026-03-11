from fastapi import APIRouter
from typing import List
from schemas import SectorSchema
import random

router = APIRouter()


@router.get("/", response_model=List[SectorSchema])
def get_sectors():
    # Mock data for now, could be aggregated from DB or analysis service
    sectors = [
        "Technology",
        "Healthcare",
        "Financials",
        "Consumer Discretionary",
        "Communication Services",
        "Industrials",
        "Consumer Staples",
        "Energy",
        "Utilities",
        "Real Estate",
        "Materials",
    ]
    return [
        SectorSchema(
            sector=sec,
            avg_score=round(random.uniform(30.0, 80.0), 2),
            ticker_count=random.randint(10, 100),
        )
        for sec in sectors
    ]
