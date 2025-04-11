import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import io
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_file(file_path: str) -> Dict[str, Any]:
    """
    Process a file using OCR to extract text
    
    Args:
        file_path: Path to the file to process
        
    Returns:
        Dictionary containing the extracted text and metadata
    """
    try:
        # Get file extension
        file_ext = Path(file_path).suffix.lower()
        
        # Process based on file type
        if file_ext in ['.pdf']:
            return await process_pdf(file_path)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']:
            return await process_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        raise

async def process_pdf(file_path: str) -> Dict[str, Any]:
    """
    Process a PDF file using Google Cloud Vision API
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Dictionary containing the extracted text and metadata
    """
    try:
        # Check if Google Cloud credentials are available
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            return await process_with_google_vision(file_path, "pdf")
        else:
            # Fallback to mock implementation for development
            return await mock_ocr_process(file_path, "pdf")
    except Exception as e:
        logger.error(f"Error processing PDF {file_path}: {str(e)}")
        raise

async def process_image(file_path: str) -> Dict[str, Any]:
    """
    Process an image file using Google Cloud Vision API
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Dictionary containing the extracted text and metadata
    """
    try:
        # Check if Google Cloud credentials are available
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            return await process_with_google_vision(file_path, "image")
        else:
            # Fallback to mock implementation for development
            return await mock_ocr_process(file_path, "image")
    except Exception as e:
        logger.error(f"Error processing image {file_path}: {str(e)}")
        raise

async def process_with_google_vision(file_path: str, file_type: str) -> Dict[str, Any]:
    """
    Process a file using Google Cloud Vision API
    
    Args:
        file_path: Path to the file
        file_type: Type of file (pdf or image)
        
    Returns:
        Dictionary containing the extracted text and metadata
    """
    try:
        # Import Google Cloud Vision
        from google.cloud import vision
        
        # Create a client
        client = vision.ImageAnnotatorClient()
        
        # Read the file
        with io.open(file_path, 'rb') as image_file:
            content = image_file.read()
        
        # Create an image object
        image = vision.Image(content=content)
        
        # Perform text detection
        response = client.text_detection(image=image)
        texts = response.text_annotations
        
        # Extract full text
        full_text = texts[0].description if texts else ""
        
        # Extract text blocks
        text_blocks = []
        for text in texts[1:]:
            text_blocks.append({
                "text": text.description,
                "bounding_box": [
                    {"x": vertex.x, "y": vertex.y}
                    for vertex in text.bounding_poly.vertices
                ]
            })
        
        # Save processed result
        processed_folder = os.getenv("PROCESSED_FOLDER", "data/processed")
        os.makedirs(processed_folder, exist_ok=True)
        
        output_file = os.path.join(
            processed_folder,
            f"{Path(file_path).stem}_ocr.json"
        )
        
        result = {
            "file_path": file_path,
            "file_type": file_type,
            "full_text": full_text,
            "text_blocks": text_blocks,
            "language": "en",  # Default to English, will be updated by language detection
            "page_count": 1 if file_type == "image" else None,  # For PDFs, this will be updated
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
    except Exception as e:
        logger.error(f"Error processing with Google Vision: {str(e)}")
        raise

async def mock_ocr_process(file_path: str, file_type: str) -> Dict[str, Any]:
    """
    Mock OCR processing for development without Google Cloud credentials
    
    Args:
        file_path: Path to the file
        file_type: Type of file (pdf or image)
        
    Returns:
        Dictionary containing mock extracted text and metadata
    """
    logger.warning("Using mock OCR processing. For production, set up Google Cloud Vision API.")
    
    # Create a mock result
    if file_type == "pdf":
        mock_text = """
        Mathematics Test Paper
        
        1. Solve the equation: 2x + 5 = 15 [2 marks]
        2. Find the derivative of f(x) = x^3 + 2x^2 - 4x + 7 [3 marks]
        3. Calculate the area of a circle with radius 5 cm. [2 marks]
        
        Section B: Subjective Questions
        
        4. Prove that the sum of the angles in a triangle is 180 degrees. [5 marks]
        5. Solve the system of equations:
           3x + 2y = 12
           x - y = 1
           Show all your work. [5 marks]
        
        Section C: Practical Application
        
        6. A rectangular garden has a length that is twice its width. If the perimeter of the garden is 60 meters, find its dimensions and area. [8 marks]
        """
    else:  # image
        mock_text = """
        Science Quiz
        
        1. What is the chemical symbol for water? [1 mark]
        2. Name the process by which plants make their own food. [1 mark]
        3. What is Newton's First Law of Motion? [2 marks]
        
        Short Answer Questions:
        
        4. Explain the difference between mitosis and meiosis. [3 marks]
        5. Describe the structure of an atom. [3 marks]
        
        Practical Question:
        
        6. Design an experiment to test the effect of light on plant growth. Include your hypothesis, variables, and procedure. [5 marks]
        """
    
    # Create mock text blocks
    lines = [line.strip() for line in mock_text.split('\n') if line.strip()]
    text_blocks = []
    
    for i, line in enumerate(lines):
        text_blocks.append({
            "text": line,
            "bounding_box": [
                {"x": 100, "y": 100 + i * 30},
                {"x": 500, "y": 100 + i * 30},
                {"x": 500, "y": 130 + i * 30},
                {"x": 100, "y": 130 + i * 30}
            ]
        })
    
    # Save processed result
    processed_folder = os.getenv("PROCESSED_FOLDER", "data/processed")
    os.makedirs(processed_folder, exist_ok=True)
    
    output_file = os.path.join(
        processed_folder,
        f"{Path(file_path).stem}_ocr.json"
    )
    
    result = {
        "file_path": file_path,
        "file_type": file_type,
        "full_text": mock_text,
        "text_blocks": text_blocks,
        "language": "en",
        "page_count": 1 if file_type == "image" else 3,
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return result
