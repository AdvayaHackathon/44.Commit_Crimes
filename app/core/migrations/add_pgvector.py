import os
import logging
import sqlalchemy as sa
from sqlalchemy import text
from app.core.database import engine, init_db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_pgvector_extension():
    """Check database connection and prepare for SQLite"""
    try:
        # Create connection to test it
        with engine.connect() as conn:
            # Check if we're using SQLite
            if 'sqlite' in str(engine.url):
                logger.info("Using SQLite database, pgvector extension not needed")
                # Make sure the data directory exists
                import os
                data_dir = os.path.dirname(str(engine.url).replace('sqlite:///', ''))
                if data_dir and not os.path.exists(data_dir):
                    os.makedirs(data_dir, exist_ok=True)
                    logger.info(f"Created data directory: {data_dir}")
            else:
                # For PostgreSQL, we would add the pgvector extension here
                logger.info("Using PostgreSQL database, but skipping pgvector extension for now")
                # Uncomment the following lines when PostgreSQL with pgvector is available
                # conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                # conn.commit()
                # logger.info("Successfully added pgvector extension")

            return True

    except Exception as e:
        logger.error(f"Error adding pgvector extension: {str(e)}")
        return False

def run_migrations():
    """Run all database migrations"""
    try:
        # Add pgvector extension
        if add_pgvector_extension():
            # Initialize database tables
            init_db()
            logger.info("All migrations completed successfully")
            return True
        else:
            logger.error("Failed to add pgvector extension")
            return False

    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        return False

if __name__ == "__main__":
    run_migrations()
