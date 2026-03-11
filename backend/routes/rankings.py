from fastapi import APIRouter, HTTPException, Depends
from typing import List
from schemas import RankingSchema
from src.services.analysis_service import AnalysisService

router = APIRouter()


# Dependency to get AnalysisService instance
def get_analysis_service():
    return AnalysisService()


@router.get("/", response_model=List[RankingSchema])
def get_rankings(service: AnalysisService = Depends(get_analysis_service)):
    try:
        analyses = service.run_full_analysis()
        return analyses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
