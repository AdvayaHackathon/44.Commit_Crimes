import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.database import get_db, DocumentChunk
from app.core.embeddings import store_document_chunks

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_processed_documents(output_folder: str = None) -> Dict[str, Any]:
    """
    Synchronize processed documents from the output folder with the database
    
    Args:
        output_folder: Path to the output folder, defaults to OUTPUT_FOLDER env var
        
    Returns:
        Dictionary containing sync results
    """
    try:
        # Get output folder path
        if output_folder is None:
            output_folder = os.getenv("OUTPUT_FOLDER", "data/output")
            
        if not os.path.exists(output_folder):
            return {
                "status": "error",
                "message": f"Output folder not found: {output_folder}",
                "synced_files": 0,
                "updated_files": 0
            }
            
        # Get all JSON files in output folder
        json_files = [f for f in os.listdir(output_folder) if f.endswith('_ocr.json')]
        
        if not json_files:
            return {
                "status": "success",
                "message": "No new files to sync",
                "synced_files": 0,
                "updated_files": 0
            }
            
        synced_count = 0
        updated_count = 0
        
        # Process each file
        with get_db() as db:
            for json_file in json_files:
                try:
                    file_path = os.path.join(output_folder, json_file)
                    
                    # Get file modification time
                    file_mtime = datetime.fromtimestamp(
                        os.path.getmtime(file_path),
                        tz=timezone.utc
                    )
                    
                    # Check if file needs processing
                    if needs_processing(db, json_file, file_mtime):
                        # Process and store document
                        process_result = process_document(db, file_path)
                        
                        if process_result["status"] == "success":
                            if process_result["action"] == "created":
                                synced_count += 1
                            else:  # updated
                                updated_count += 1
                except Exception as e:
                    logger.error(f"Error processing file {json_file}: {str(e)}")
                    continue
                    
        return {
            "status": "success",
            "message": f"Synced {synced_count} new files, updated {updated_count} files",
            "synced_files": synced_count,
            "updated_files": updated_count
        }
                    
    except Exception as e:
        logger.error(f"Error in sync_processed_documents: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "synced_files": 0,
            "updated_files": 0
        }

def needs_processing(db: Session, file_name: str, file_mtime: datetime) -> bool:
    """
    Check if a file needs processing based on its modification time
    
    Args:
        db: Database session
        file_name: Name of the file
        file_mtime: File's modification time
        
    Returns:
        True if file needs processing, False otherwise
    """
    try:
        # Get latest chunk for this file
        latest_chunk = db.query(DocumentChunk)\
            .filter(DocumentChunk.file_name.like(f"%{file_name}%"))\
            .order_by(DocumentChunk.created_at.desc())\
            .first()
            
        if not latest_chunk:
            return True  # New file, needs processing
            
        # Compare modification times
        return file_mtime > latest_chunk.created_at
        
    except Exception as e:
        logger.error(f"Error checking if file needs processing: {str(e)}")
        return True  # Process file on error to be safe

def process_document(db: Session, file_path: str) -> Dict[str, str]:
    """
    Process a document and store it in the database
    
    Args:
        db: Database session
        file_path: Path to the document file
        
    Returns:
        Dictionary with processing status and action taken
    """
    try:
        # Read document content
        with open(file_path, 'r', encoding='utf-8') as f:
            doc_data = json.loads(f.read())
            
        # Store document chunks
        chunk_ids = store_document_chunks(
            file_path=doc_data["file_path"],
            text=doc_data["full_text"],
            metadata={
                "language": doc_data.get("language", "en"),
                "file_type": doc_data.get("file_type", "unknown"),
                "processed_at": datetime.now(timezone.utc).isoformat()
            },
            db=db
        )
        
        return {
            "status": "success",
            "action": "created" if len(chunk_ids) > 0 else "updated"
        }
        
    except Exception as e:
        logger.error(f"Error processing document {file_path}: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }