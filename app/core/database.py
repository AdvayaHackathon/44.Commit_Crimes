import os
import logging
import json
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from contextlib import contextmanager

# Import pgvector extension
import numpy as np
from pgvector.sqlalchemy import Vector

# Set up logging
logger = logging.getLogger(__name__)

# Get database URL from environment variable or use default
# Fall back to SQLite if PostgreSQL is not available
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

# Create SQLAlchemy engine
try:
    engine = create_engine(DATABASE_URL)
    logger.info(f"Database connection established")
except Exception as e:
    logger.error(f"Error connecting to database: {str(e)}")
    raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

@contextmanager
def get_db():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define database models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), nullable=False)  # 'student' or 'teacher'
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.now(datetime.timezone.utc))

    # Relationships
    test_plans = relationship("TestPlan", back_populates="user")
    study_plans = relationship("StudyPlan", back_populates="user")

class TestPlan(Base):
    __tablename__ = "test_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    test_date = Column(DateTime, nullable=False)
    test_type = Column(String(50))
    duration = Column(Integer)  # in minutes
    total_marks = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.now(datetime.timezone.utc))

    # Relationships
    user = relationship("User", back_populates="test_plans")
    questions = relationship("TestQuestion", back_populates="test_plan")

class TestQuestion(Base):
    __tablename__ = "test_questions"

    id = Column(Integer, primary_key=True, index=True)
    test_plan_id = Column(Integer, ForeignKey("test_plans.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50))  # 'objective', 'subjective', 'practical'
    marks = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc))

    # Relationships
    test_plan = relationship("TestPlan", back_populates="questions")

class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    day_number = Column(Integer, nullable=False)
    plan_date = Column(DateTime, nullable=False)
    topics = Column(Text)  # JSON string of topics
    time_allocation = Column(Text)  # JSON string of time allocations
    practice = Column(Text)  # JSON string of practice exercises
    key_concepts = Column(Text)  # JSON string of key concepts
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.now(datetime.timezone.utc))

    # Relationships
    user = relationship("User", back_populates="study_plans")

class ExamType(Base):
    __tablename__ = "exam_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    duration_months = Column(Integer)  # Typical preparation duration in months
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc))

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(255), index=True)  # Original file identifier
    file_name = Column(String(255))  # Original file name
    chunk_index = Column(Integer)  # Index of the chunk within the document
    content = Column(Text, nullable=False)  # Text content of the chunk
    chunk_metadata = Column(Text)  # Additional metadata as JSON string
    embedding_data = Column(Text)  # Vector embedding as JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc))

def init_db():
    """Initialize the database by creating all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        # Create initial exam types if they don't exist
        with get_db() as db:
            if db.query(ExamType).count() == 0:
                initial_exams = [
                    ExamType(name="GATE CSE", description="Graduate Aptitude Test in Engineering for Computer Science", duration_months=6),
                    ExamType(name="JEE", description="Joint Entrance Examination for Engineering", duration_months=12),
                    ExamType(name="NEET", description="National Eligibility cum Entrance Test for Medical", duration_months=12),
                    ExamType(name="UPSC", description="Union Public Service Commission for Civil Services", duration_months=12),
                    ExamType(name="GRE", description="Graduate Record Examination for Graduate Studies", duration_months=3)
                ]
                db.add_all(initial_exams)
                db.commit()
                logger.info("Initial exam types created")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
