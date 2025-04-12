import os
import shutil
import asyncio
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from app.core.ocr.folder_processor import process_folder
from app.models.folder import FolderProcessRequest, FolderProcessResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/folder",
    tags=["folder"],
    responses={404: {"description": "Not found"}},
)

@router.post("/process", response_model=FolderProcessResponse)
async def process_folder_path(
    request: Request,
    folder_request: FolderProcessRequest,
):
    """
    Process all files in a folder
    """
    try:
        # Get folder path
        folder_path = folder_request.folder_path
        
        # Check if folder exists
        if not os.path.isdir(folder_path):
            raise HTTPException(status_code=400, detail=f"Folder not found: {folder_path}")
        
        # Process folder
        result = await process_folder(
            folder_path=folder_path,
            recursive=folder_request.recursive,
            exam_type=folder_request.exam_type,
            exam_date=folder_request.exam_date
        )
        
        return FolderProcessResponse(
            status="success",
            message=f"Successfully processed folder: {folder_path}",
            result=result
        )
    except Exception as e:
        logger.error(f"Error processing folder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload", response_model=FolderProcessResponse)
async def upload_folder(
    request: Request,
    files: List[UploadFile] = File(...),
    exam_type: str = Form(...),
    exam_date: str = Form(...),
):
    """
    Upload multiple files and process them as a folder
    """
    try:
        # Create a temporary folder for uploaded files
        temp_folder = os.path.join("data", "temp", f"upload_{os.urandom(4).hex()}")
        os.makedirs(temp_folder, exist_ok=True)
        
        # Save uploaded files
        for file in files:
            file_path = os.path.join(temp_folder, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        
        # Process the folder
        result = await process_folder(
            folder_path=temp_folder,
            recursive=False,
            exam_type=exam_type,
            exam_date=exam_date
        )
        
        return FolderProcessResponse(
            status="success",
            message=f"Successfully processed {len(files)} files",
            result=result
        )
    except Exception as e:
        logger.error(f"Error processing uploaded files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/exams", response_model=List[Dict[str, Any]])
async def get_exam_types():
    """
    Get list of available exam types
    """
    # This could be fetched from a database in a real application
    exam_types = [
        {
            "id": "gate_cse",
            "name": "GATE Computer Science",
            "description": "Graduate Aptitude Test in Engineering for Computer Science",
            "duration_months": 6
        },
        {
            "id": "upsc_cse",
            "name": "UPSC Civil Services",
            "description": "Union Public Service Commission Civil Services Examination",
            "duration_months": 12
        },
        {
            "id": "cat",
            "name": "CAT",
            "description": "Common Admission Test for MBA admissions",
            "duration_months": 4
        },
        {
            "id": "jee_main",
            "name": "JEE Main",
            "description": "Joint Entrance Examination for engineering colleges",
            "duration_months": 6
        },
        {
            "id": "neet",
            "name": "NEET",
            "description": "National Eligibility cum Entrance Test for medical colleges",
            "duration_months": 6
        },
        {
            "id": "gre",
            "name": "GRE",
            "description": "Graduate Record Examination for graduate school admissions",
            "duration_months": 3
        },
        {
            "id": "gmat",
            "name": "GMAT",
            "description": "Graduate Management Admission Test for business school admissions",
            "duration_months": 3
        }
    ]
    
    return exam_types
