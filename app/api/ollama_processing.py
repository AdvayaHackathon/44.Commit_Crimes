import os
import logging
import tempfile
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from app.core.ollama.processor import (
    process_files_with_ollama,
    generate_test_plan_with_ollama,
    generate_daily_content_with_ollama
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/ollama",
    tags=["ollama"],
    responses={404: {"description": "Not found"}},
)

@router.post("/process")
async def process_files(
    files: List[UploadFile] = File(...),
    task_description: str = Form(...),
    exam_type: Optional[str] = Form(None),
    model: str = Form("deepseek-r1:1.5b")
):
    """
    Process multiple files using Ollama
    """
    try:
        # Create temporary directory for files
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = []
            
            # Save uploaded files to temporary directory
            for file in files:
                file_path = os.path.join(temp_dir, file.filename)
                with open(file_path, "wb") as f:
                    f.write(await file.read())
                file_paths.append(file_path)
            
            # Process files
            result = process_files_with_ollama(
                file_paths=file_paths,
                task_description=task_description,
                model=model,
                exam_type=exam_type
            )
            
            return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error processing files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")

@router.post("/test-plan")
async def generate_test_plan(
    files: List[UploadFile] = File(...),
    exam_type: Optional[str] = Form(None),
    model: str = Form("deepseek-r1:1.5b")
):
    """
    Generate a test plan from multiple files using Ollama
    """
    try:
        # Create temporary directory for files
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = []
            
            # Save uploaded files to temporary directory
            for file in files:
                file_path = os.path.join(temp_dir, file.filename)
                with open(file_path, "wb") as f:
                    f.write(await file.read())
                file_paths.append(file_path)
            
            # Generate test plan
            result = generate_test_plan_with_ollama(
                file_paths=file_paths,
                exam_type=exam_type,
                model=model
            )
            
            return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error generating test plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating test plan: {str(e)}")

@router.post("/daily-content")
async def generate_daily_content(
    files: List[UploadFile] = File(...),
    exam_type: Optional[str] = Form(None),
    model: str = Form("deepseek-r1:1.5b")
):
    """
    Generate daily study content from multiple files using Ollama
    """
    try:
        # Create temporary directory for files
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = []
            
            # Save uploaded files to temporary directory
            for file in files:
                file_path = os.path.join(temp_dir, file.filename)
                with open(file_path, "wb") as f:
                    f.write(await file.read())
                file_paths.append(file_path)
            
            # Generate daily content
            result = generate_daily_content_with_ollama(
                file_paths=file_paths,
                exam_type=exam_type,
                model=model
            )
            
            return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error generating daily content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating daily content: {str(e)}")

@router.get("/models")
async def list_models():
    """
    List available Ollama models
    """
    try:
        from app.core.ollama.client import ollama_client
        models = ollama_client.list_models()
        return JSONResponse(content={"models": models})
    
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing models: {str(e)}")

@router.get("/status")
async def check_status():
    """
    Check Ollama server status
    """
    try:
        from app.core.ollama.client import ollama_client
        status = ollama_client.test_connection()
        return JSONResponse(content={"status": "connected" if status else "disconnected"})
    
    except Exception as e:
        logger.error(f"Error checking Ollama status: {str(e)}")
        return JSONResponse(content={"status": "disconnected", "error": str(e)})
