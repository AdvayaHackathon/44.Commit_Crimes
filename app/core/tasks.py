import asyncio
import logging
import time
from datetime import datetime
from app.core.utils.cleanup import clean_temp_folder

# Set up logging
logger = logging.getLogger(__name__)

# Global flag to track if the background task is running
background_task_running = False

async def periodic_cleanup(interval_hours=6):
    """
    Periodically clean up temporary files
    
    Args:
        interval_hours: Interval between cleanups in hours
    """
    global background_task_running
    
    if background_task_running:
        logger.info("Periodic cleanup task is already running")
        return
    
    background_task_running = True
    
    try:
        logger.info(f"Starting periodic cleanup task (interval: {interval_hours} hours)")
        
        while True:
            # Sleep first to avoid cleanup right at startup
            await asyncio.sleep(interval_hours * 3600)  # Convert hours to seconds
            
            try:
                # Clean up files older than 24 hours
                start_time = time.time()
                files_deleted, bytes_freed = clean_temp_folder(max_age_hours=24)
                duration = time.time() - start_time
                
                if files_deleted > 0:
                    logger.info(f"Periodic cleanup: removed {files_deleted} files, freed {bytes_freed/1024:.2f} KB in {duration:.2f} seconds")
                else:
                    logger.info(f"Periodic cleanup: no files to remove (completed in {duration:.2f} seconds)")
            
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {str(e)}")
    
    except asyncio.CancelledError:
        logger.info("Periodic cleanup task cancelled")
    
    except Exception as e:
        logger.error(f"Unexpected error in periodic cleanup task: {str(e)}")
    
    finally:
        background_task_running = False

def start_background_tasks():
    """Start all background tasks"""
    asyncio.create_task(periodic_cleanup())
