from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class FileResponse(BaseModel):
    """
    Response model for file upload
    """
    filename: str
    file_path: str
    status: str
    message: str
    result: Optional[Dict[str, Any]] = None
