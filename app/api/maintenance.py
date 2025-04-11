import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from app.core.utils.cleanup import clean_all_temp_files, clean_temp_folder

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/maintenance",
    tags=["maintenance"],
    responses={404: {"description": "Not found"}},
)

@router.post("/cleanup/temp")
async def cleanup_temp_files(max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Clean up temporary files older than the specified age
    
    Args:
        max_age_hours: Maximum age of files to keep (in hours)
        
    Returns:
        Dict with cleanup results
    """
    try:
        files_deleted, bytes_freed = clean_temp_folder(max_age_hours=max_age_hours)
        
        return {
            "status": "success",
            "message": f"Cleaned up {files_deleted} temporary files",
            "files_deleted": files_deleted,
            "bytes_freed": bytes_freed,
            "kb_freed": round(bytes_freed / 1024, 2)
        }
    except Exception as e:
        logger.error(f"Error cleaning temp files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error cleaning temp files: {str(e)}")

@router.post("/cleanup/temp/all")
async def cleanup_all_temp_files() -> Dict[str, Any]:
    """
    Remove all files from the temp folder
    
    Returns:
        Dict with cleanup status
    """
    try:
        success = clean_all_temp_files()
        
        if success:
            return {
                "status": "success",
                "message": "All temporary files have been removed"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to remove all temporary files"
            }
    except Exception as e:
        logger.error(f"Error cleaning all temp files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error cleaning all temp files: {str(e)}")
