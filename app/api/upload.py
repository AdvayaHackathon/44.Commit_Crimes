import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import JSONResponse
from typing import List
from pathlib import Path
from app.core.ocr.processor import process_file
from app.models.file import FileResponse

router = APIRouter(
    prefix="/api/upload",
    tags=["upload"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=FileResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
):
    """
    Upload a file for OCR processing
    """
    try:
        # Get input folder from environment variables
        input_folder = os.getenv("INPUT_FOLDER", "data/input")
        
        # Create folder if it doesn't exist
        os.makedirs(input_folder, exist_ok=True)
        
        # Save file to input folder
        file_path = os.path.join(input_folder, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process file with OCR
        result = await process_file(file_path)
        
        return FileResponse(
            filename=file.filename,
            file_path=file_path,
            status="success",
            message="File uploaded successfully",
            result=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch", response_model=List[FileResponse])
async def upload_batch(
    request: Request,
    files: List[UploadFile] = File(...),
):
    """
    Upload multiple files for batch OCR processing
    """
    results = []
    
    for file in files:
        try:
            # Get input folder from environment variables
            input_folder = os.getenv("INPUT_FOLDER", "data/input")
            
            # Create folder if it doesn't exist
            os.makedirs(input_folder, exist_ok=True)
            
            # Save file to input folder
            file_path = os.path.join(input_folder, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Process file with OCR
            result = await process_file(file_path)
            
            results.append(
                FileResponse(
                    filename=file.filename,
                    file_path=file_path,
                    status="success",
                    message="File uploaded successfully",
                    result=result
                )
            )
        except Exception as e:
            results.append(
                FileResponse(
                    filename=file.filename,
                    file_path="",
                    status="error",
                    message=str(e),
                    result=None
                )
            )
    
    return results
