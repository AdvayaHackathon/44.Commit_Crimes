import os
import logging
from typing import Optional
import PyPDF2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from a file based on its type.
    Currently supports: PDF files
    
    Args:
        file_path: Path to the file
        
    Returns:
        Extracted text from the file
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return f"Error: File not found: {file_path}"
        
        # Get file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Process PDF files
        if file_ext == '.pdf':
            return extract_text_from_pdf(file_path)
        
        # Process text files
        elif file_ext in ['.txt', '.md', '.rst']:
            return extract_text_from_text_file(file_path)
        
        else:
            return f"Error: Unsupported file type: {file_ext}"
    
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        return f"Error: {str(e)}"

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file using PyPDF2
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text from the PDF
    """
    try:
        text = []
        
        # Open PDF file
        with open(file_path, 'rb') as file:
            # Create PDF reader object
            reader = PyPDF2.PdfReader(file)
            
            # Extract text from each page
            for page in reader.pages:
                text.append(page.extract_text())
        
        # Join all pages with newlines
        return '\n'.join(text)
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        return f"Error: {str(e)}"

def extract_text_from_text_file(file_path: str) -> str:
    """
    Extract text from a text file
    
    Args:
        file_path: Path to the text file
        
    Returns:
        Content of the text file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    except Exception as e:
        logger.error(f"Error reading text file {file_path}: {str(e)}")
        return f"Error: {str(e)}"