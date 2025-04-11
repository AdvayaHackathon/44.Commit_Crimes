import os
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

def clean_temp_folder(max_age_hours=24):
    """
    Clean up temporary files from the data/temp folder
    
    Args:
        max_age_hours: Maximum age of files to keep (in hours)
        
    Returns:
        tuple: (number of files deleted, total size freed in bytes)
    """
    try:
        # Get temp folder path
        temp_folder = os.path.join("data", "temp")
        
        # Check if folder exists
        if not os.path.exists(temp_folder):
            logger.warning(f"Temp folder not found: {temp_folder}")
            return 0, 0
        
        # Calculate cutoff time
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Track statistics
        files_deleted = 0
        bytes_freed = 0
        
        # Iterate through files in temp folder
        for item in os.listdir(temp_folder):
            item_path = os.path.join(temp_folder, item)
            
            # Skip directories for now
            if os.path.isdir(item_path):
                continue
            
            # Check file modification time
            mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
            
            # Delete files older than cutoff time
            if mtime < cutoff_time:
                # Get file size before deleting
                file_size = os.path.getsize(item_path)
                
                try:
                    os.remove(item_path)
                    files_deleted += 1
                    bytes_freed += file_size
                    logger.info(f"Deleted temp file: {item}")
                except Exception as e:
                    logger.error(f"Error deleting temp file {item}: {str(e)}")
        
        # Clean empty subdirectories
        for root, dirs, files in os.walk(temp_folder, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                if not os.listdir(dir_path):  # Check if directory is empty
                    try:
                        os.rmdir(dir_path)
                        logger.info(f"Removed empty directory: {dir_path}")
                    except Exception as e:
                        logger.error(f"Error removing directory {dir_path}: {str(e)}")
        
        logger.info(f"Temp folder cleanup: {files_deleted} files deleted, {bytes_freed/1024:.2f} KB freed")
        return files_deleted, bytes_freed
    
    except Exception as e:
        logger.error(f"Error cleaning temp folder: {str(e)}")
        return 0, 0

def clean_all_temp_files():
    """
    Remove all files and subdirectories from the temp folder
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get temp folder path
        temp_folder = os.path.join("data", "temp")
        
        # Check if folder exists
        if not os.path.exists(temp_folder):
            logger.warning(f"Temp folder not found: {temp_folder}")
            return True
        
        # Delete all contents
        for item in os.listdir(temp_folder):
            item_path = os.path.join(temp_folder, item)
            
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    logger.info(f"Deleted temp file: {item}")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    logger.info(f"Deleted temp directory: {item}")
            except Exception as e:
                logger.error(f"Error deleting temp item {item}: {str(e)}")
        
        logger.info("All temporary files cleaned")
        return True
    
    except Exception as e:
        logger.error(f"Error cleaning all temp files: {str(e)}")
        return False
