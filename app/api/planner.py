from fastapi import APIRouter, HTTPException, Request, Body
from typing import List, Dict, Any
from app.core.planner.test_planner import generate_test_plan
from app.models.planner import PlannerRequest, PlannerResponse
import os
import json
import glob
from datetime import datetime

router = APIRouter(
    prefix="/api",
    tags=["planner"],
    responses={404: {"description": "Not found"}},
)

@router.post("/planner", response_model=PlannerResponse)
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

@router.get("/daily-content")
async def get_daily_content():
    try:
        # Get the absolute path to the data/output directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(base_dir, 'data', 'output')
        
        # Get all daily content files
        pattern = os.path.join(output_dir, 'daily_content_*.json')
        matching_files = glob.glob(pattern)
        
        if not matching_files:
            raise HTTPException(status_code=404, detail="No content found")
        
        # Get the most recent file
        latest_file = max(matching_files, key=os.path.getctime)
        
        # Read the JSON content
        with open(latest_file, 'r', encoding='utf-8') as f:
            content = json.load(f)
            
            # Add metadata about the file
            content['source_file'] = os.path.basename(latest_file)
            return {
                'status': 'success',
                'data': content,
                'file_info': {
                    'name': os.path.basename(latest_file),
                    'created': datetime.fromtimestamp(os.path.getctime(latest_file)).isoformat(),
                    'path': latest_file
                }
            }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
