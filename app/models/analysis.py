from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class AnalysisRequest(BaseModel):
    """
    Request model for text analysis
    """
    text: str
    language: str = "en"
    file_type: str = "pdf"

class AnalysisResponse(BaseModel):
    """
    Response model for text analysis
    """
    status: str
    message: str
    result: Optional[Dict[str, Any]] = None
