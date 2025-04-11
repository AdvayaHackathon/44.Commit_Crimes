from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class PlannerRequest(BaseModel):
    """
    Request model for test planner
    """
    analysis_results: List[Dict[str, Any]]
    test_type: str = "mixed"
    duration: int = 60
    total_marks: int = 100

class PlannerResponse(BaseModel):
    """
    Response model for test planner
    """
    status: str
    message: str
    plan: Optional[Dict[str, Any]] = None
