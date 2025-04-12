import os
import logging
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.core.ollama.client import ollama_client
from app.core.ocr.document_processor import extract_text_from_file

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_files_with_ollama(
    file_paths: List[str],
    task_description: str,
    model: str = "deepseek-r1:1.5b",
    exam_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process multiple files using Ollama
    
    Args:
        file_paths: List of file paths to process
        task_description: Description of the task to perform
        model: Ollama model to use
        exam_type: Type of exam (for context)
        
    Returns:
        Dictionary with processing results
    """
    try:
        # Extract text from all files
        file_contents = []
        
        for file_path in file_paths:
            try:
                # Get file name
                file_name = os.path.basename(file_path)
                
                # Extract text based on file type
                extracted_text = extract_text_from_file(file_path)
                
                if "Error:" in extracted_text:
                    logger.warning(f"Error extracting text from {file_name}: {extracted_text}")
                    continue
                
                # Add to file contents list
                file_contents.append({
                    "file_name": file_name,
                    "content": extracted_text
                })
                
                logger.info(f"Successfully extracted text from {file_name}")
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
        
        if not file_contents:
            return {
                "status": "error",
                "message": "No text could be extracted from the provided files",
                "files_processed": 0
            }
        
        # Enhance task description with exam type if provided
        enhanced_task = task_description
        if exam_type:
            enhanced_task = f"{task_description} for {exam_type} exam"
        
        # Process files with Ollama
        result = ollama_client.process_multiple_files(
            file_contents=file_contents,
            task_description=enhanced_task,
            model=model
        )
        
        # Add number of files processed
        result["files_processed"] = len(file_contents)
        
        return result
    
    except Exception as e:
        logger.error(f"Error in process_files_with_ollama: {str(e)}")
        return {
            "status": "error",
            "message": f"Error processing files: {str(e)}",
            "files_processed": 0
        }

def generate_test_plan_with_ollama(
    file_paths: List[str],
    exam_type: Optional[str] = None,
    model: str = "deepseek-r1:1.5b"
) -> Dict[str, Any]:
    """
    Generate a test plan from multiple files using Ollama
    
    Args:
        file_paths: List of file paths to process
        exam_type: Type of exam
        model: Ollama model to use
        
    Returns:
        Dictionary with test plan
    """
    task_description = """
    Analyze the educational content in these files and create a comprehensive test plan.
    The test plan should include:
    1. Objective questions (multiple choice, true/false)
    2. Subjective questions (short answer, essay)
    3. Practical exercises
    
    For each section, provide at least 5 questions or exercises that test understanding of the material.
    Organize the test plan by topics and include a suggested time allocation for each section.
    """
    
    return process_files_with_ollama(
        file_paths=file_paths,
        task_description=task_description,
        model=model,
        exam_type=exam_type
    )

def generate_daily_content_with_ollama(
    file_paths: List[str],
    exam_type: Optional[str] = None,
    model: str = "deepseek-r1:1.5b"
) -> Dict[str, Any]:
    """
    Generate daily study content from multiple files using Ollama
    
    Args:
        file_paths: List of file paths to process
        exam_type: Type of exam
        model: Ollama model to use
        
    Returns:
        Dictionary with daily content plan
    """
    task_description = """
    Create a daily study plan based on the educational content in these files.
    The study plan should include:
    1. Topics to cover each day
    2. Time allocation for each topic
    3. Practice exercises or questions
    4. Review strategies
    
    Create a plan for 8 days, with each day having a clear focus and achievable goals.
    """
    
    return process_files_with_ollama(
        file_paths=file_paths,
        task_description=task_description,
        model=model,
        exam_type=exam_type
    )
