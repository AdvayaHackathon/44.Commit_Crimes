from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class FolderProcessRequest(BaseModel):
    """
    Request model for folder processing
    """
    folder_path: str
    recursive: bool = False
    exam_type: str
    exam_date: str

class FolderProcessResponse(BaseModel):
    """
    Response model for folder processing
    """
    status: str
    message: str
    result: Optional[Dict[str, Any]] = None
