from fastapi import APIRouter, HTTPException, Request, Body
from typing import List, Dict, Any
from app.core.planner.test_planner import generate_test_plan
from app.models.planner import PlannerRequest, PlannerResponse

router = APIRouter(
    prefix="/api/planner",
    tags=["planner"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=PlannerResponse)
async def create_test_plan(
    request: Request,
    planner_request: PlannerRequest = Body(...),
):
    """
    Generate a test plan based on analyzed content
    """
    try:
        # Generate test plan
        plan = await generate_test_plan(
            analysis_results=planner_request.analysis_results,
            test_type=planner_request.test_type,
            duration=planner_request.duration,
            total_marks=planner_request.total_marks
        )
        
        return PlannerResponse(
            status="success",
            message="Test plan generated successfully",
            plan=plan
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/daily-report", response_model=Dict[str, Any])
async def generate_daily_report(
    request: Request,
    analysis_results: List[Dict[str, Any]] = Body(...),
):
    """
    Generate a daily report based on analyzed content
    """
    try:
        # TODO: Implement daily report generation
        report = {
            "date": "2023-11-01",
            "total_files_processed": len(analysis_results),
            "topics_covered": ["Math", "Science", "History"],
            "question_distribution": {
                "objective": 45,
                "subjective": 35,
                "practical": 20
            },
            "learning_outcomes": [
                {"topic": "Math", "mastery_level": 0.85},
                {"topic": "Science", "mastery_level": 0.72},
                {"topic": "History", "mastery_level": 0.68}
            ]
        }
        
        return {
            "status": "success",
            "message": "Daily report generated successfully",
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
