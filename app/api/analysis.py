from fastapi import APIRouter, HTTPException, Request, Body
from typing import List, Dict, Any
from app.core.analysis.text_analyzer import analyze_text
from app.models.analysis import AnalysisRequest, AnalysisResponse

router = APIRouter(
    prefix="/api/analysis",
    tags=["analysis"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=AnalysisResponse)
async def analyze_content(
    request: Request,
    analysis_request: AnalysisRequest = Body(...),
):
    """
    Analyze extracted text content
    """
    try:
        # Perform text analysis
        result = await analyze_text(
            text=analysis_request.text,
            language=analysis_request.language,
            file_type=analysis_request.file_type
        )
        
        return AnalysisResponse(
            status="success",
            message="Analysis completed successfully",
            result=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch", response_model=List[AnalysisResponse])
async def analyze_batch(
    request: Request,
    analysis_requests: List[AnalysisRequest] = Body(...),
):
    """
    Analyze multiple text contents in batch
    """
    results = []
    
    for analysis_request in analysis_requests:
        try:
            # Perform text analysis
            result = await analyze_text(
                text=analysis_request.text,
                language=analysis_request.language,
                file_type=analysis_request.file_type
            )
            
            results.append(
                AnalysisResponse(
                    status="success",
                    message="Analysis completed successfully",
                    result=result
                )
            )
        except Exception as e:
            results.append(
                AnalysisResponse(
                    status="error",
                    message=str(e),
                    result=None
                )
            )
    
    return results
