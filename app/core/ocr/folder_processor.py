import os
import base64
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import google.generativeai as genai
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Import document chunking and embedding functionality
from app.core.embeddings import store_document_chunks, search_similar_chunks
from app.core.database import get_db

# Import cleanup utilities
from app.core.utils.cleanup import clean_temp_folder, clean_all_temp_files

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supported file formats and their MIME types
MIME_MAP = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.webp': 'image/webp',
    '.pdf': 'application/pdf'  # PDF support
}

async def process_folder(
    folder_path: str,
    recursive: bool = False,
    exam_type: str = "",
    exam_date: str = ""
) -> Dict[str, Any]:
    """
    Process all files in a folder using Google Gemini model

    Args:
        folder_path: Path to the folder containing files to process
        recursive: Whether to process subfolders recursively
        exam_type: Type of exam the user is preparing for
        exam_date: Date when the user will take the exam

    Returns:
        Dictionary containing processing results
    """
    try:
        logger.info(f"Processing folder: {folder_path}")

        # Configure Google Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        genai.configure(api_key=api_key)

        # Initialize model
        model = genai.GenerativeModel("gemini-1.5-pro")

        # Get all files
        files = []
        if recursive:
            for root, _, filenames in os.walk(folder_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    files.append(file_path)
        else:
            files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
                    if os.path.isfile(os.path.join(folder_path, f))]

        # Filter files by extension
        valid_files = []
        for file_path in files:
            ext = Path(file_path).suffix.lower()
            if ext in MIME_MAP:
                valid_files.append(file_path)

        logger.info(f"Found {len(valid_files)} valid files to process")

        # Process files in batches
        BATCH_SIZE = 2  # Process two files at a time
        all_results = []

        for i in range(0, len(valid_files), BATCH_SIZE):
            batch_files = valid_files[i:i + BATCH_SIZE]

            logger.info(f"Processing batch {i//BATCH_SIZE + 1} with {len(batch_files)} files...")

            # Prepare batch payloads
            batch_payloads = []
            batch_paths = []

            for file_path in batch_files:
                ext = Path(file_path).suffix.lower()
                mime_type = MIME_MAP[ext]

                try:
                    # Read file bytes
                    with open(file_path, "rb") as f:
                        file_data = f.read()

                    # Create payload
                    payload = {
                        'mime_type': mime_type,
                        'data': base64.b64encode(file_data).decode('utf-8')
                    }

                    batch_payloads.append(payload)
                    batch_paths.append(file_path)
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {str(e)}")

            if not batch_payloads:
                continue

            try:
                # Prepare prompt based on file type
                prompt = """
                Analyze the provided files. For each file:
                1. Extract all visible text content
                2. If tables are detected, convert them to structured format
                3. Identify key concepts, formulas, and important points
                4. Organize the content by topics and subtopics
                5. Format the output in a clean, readable structure
                """

                # Send to model
                contents = [prompt] + batch_payloads
                response = await asyncio.to_thread(
                    lambda: model.generate_content(contents)
                )

                # Process response
                extracted_text = response.text.strip()

                # Store in database with vector embeddings
                with get_db() as db:
                    for path in batch_paths:
                        # Create metadata for the document
                        metadata = {
                            "exam_type": exam_type,
                            "exam_date": exam_date,
                            "file_type": os.path.splitext(path)[1].lower(),
                            "processed_at": datetime.now().isoformat()
                        }

                        # Store document chunks with embeddings
                        chunk_ids = store_document_chunks(
                            file_path=path,
                            text=extracted_text,
                            metadata=metadata,
                            db=db
                        )

                        # Add to results
                        result = {
                            "file_path": path,
                            "file_name": os.path.basename(path),
                            "extracted_text": extracted_text,
                            "processed_at": datetime.now().isoformat(),
                            "chunk_ids": chunk_ids,
                            "chunks_count": len(chunk_ids)
                        }
                        all_results.append(result)

                logger.info(f"Successfully processed batch {i//BATCH_SIZE + 1}")
            except Exception as e:
                logger.error(f"Error processing batch {i//BATCH_SIZE + 1}: {str(e)}")
                # Add empty results for failed batch
                for path in batch_paths:
                    result = {
                        "file_path": path,
                        "file_name": os.path.basename(path),
                        "extracted_text": f"Error: Failed to process file",
                        "processed_at": datetime.now().isoformat()
                    }
                    all_results.append(result)

        # Save results
        output_folder = os.getenv("OUTPUT_FOLDER", "data/output")
        os.makedirs(output_folder, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_folder, f"folder_results_{timestamp}.json")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        # Generate test plans and study materials based on extracted content
        test_plans = await generate_test_plans(all_results, exam_type, exam_date)
        daily_content = await generate_daily_content(all_results, exam_type, exam_date)
        motivational_quotes = await get_motivational_quotes()

        # Combine all results
        final_result = {
            "processed_files": len(all_results),
            "output_file": output_file,
            "exam_type": exam_type,
            "exam_date": exam_date,
            "test_plans": test_plans,
            "daily_content": daily_content,
            "motivational_quotes": motivational_quotes
        }

        # Clean up temporary files
        try:
            files_deleted, bytes_freed = clean_temp_folder(max_age_hours=1)  # Clean files older than 1 hour
            logger.info(f"Cleaned up {files_deleted} temporary files, freed {bytes_freed/1024:.2f} KB")
        except Exception as cleanup_error:
            logger.warning(f"Error cleaning temporary files: {str(cleanup_error)}")

        return final_result
    except Exception as e:
        logger.error(f"Error in folder processing: {str(e)}")
        raise

async def generate_test_plans(
    results: List[Dict[str, Any]],
    exam_type: str,
    exam_date: str
) -> List[Dict[str, Any]]:
    """
    Generate test plans based on processed content

    Args:
        results: List of processing results
        exam_type: Type of exam
        exam_date: Date of exam

    Returns:
        List of test plans
    """
    try:
        logger.info(f"Generating test plans for {exam_type}")

        # Configure Google Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        genai.configure(api_key=api_key)

        # Initialize model
        model = genai.GenerativeModel("gemini-1.5-pro")

        # Get relevant content from vector database
        with get_db() as db:
            # Create a query to find relevant content for test planning
            query = f"Create test plans for {exam_type} exam with objective, subjective, and practical questions"

            # Search for similar chunks with metadata filter for this exam type
            metadata_filter = {"exam_type": exam_type} if exam_type else None
            relevant_chunks = search_similar_chunks(
                query=query,
                top_k=10,  # Get top 10 most relevant chunks
                metadata_filter=metadata_filter,
                db=db
            )

            # Extract content from chunks
            relevant_content = "\n\n".join([chunk["content"] for chunk in relevant_chunks])

            # If no relevant content found in vector DB, fall back to results
            if not relevant_content:
                logger.warning("No relevant content found in vector database, using raw results")
                relevant_content = "\n\n".join([result["extracted_text"] for result in results
                                   if "Error:" not in result["extracted_text"]])
            else:
                logger.info(f"Found {len(relevant_chunks)} relevant chunks in vector database")

        # Calculate days until exam
        days_until_exam = 90  # Default to 90 days
        try:
            exam_date_obj = datetime.strptime(exam_date, "%Y-%m-%d")
            today = datetime.now()
            days_until_exam = (exam_date_obj - today).days
            if days_until_exam < 1:
                days_until_exam = 90  # Default if date is in the past
        except:
            logger.warning(f"Could not parse exam date: {exam_date}, using default 90 days")

        # Generate test plans
        prompt = f"""
        Based on the following educational content, create 3 different test plans for a student preparing for the {exam_type} exam in {days_until_exam} days.

        For each test plan:
        1. Create a title and description
        2. Include 10 questions with varying difficulty levels (easy, medium, hard)
        3. For each question, provide the correct answer and explanation
        4. Group questions by topic
        5. Include a time estimate for each test
        6. Format the output as a structured JSON

        Content:
        {relevant_content[:10000]}  # Limit content length to avoid token limits
        """

        response = await asyncio.to_thread(
            lambda: model.generate_content(prompt)
        )

        # Parse response as JSON
        try:
            test_plans = json.loads(response.text)
        except:
            # If not valid JSON, return as text
            test_plans = [
                {
                    "title": f"Test Plan 1 for {exam_type}",
                    "description": "Generated test plan",
                    "questions": response.text
                }
            ]

        # Save test plans
        output_folder = os.getenv("OUTPUT_FOLDER", "data/output")
        test_plans_file = os.path.join(output_folder, f"test_plans_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        with open(test_plans_file, 'w', encoding='utf-8') as f:
            json.dump(test_plans, f, ensure_ascii=False, indent=2)

        return test_plans
    except Exception as e:
        logger.error(f"Error generating test plans: {str(e)}")
        return [{"error": str(e)}]

async def generate_daily_content(
    results: List[Dict[str, Any]],
    exam_type: str,
    exam_date: str
) -> Dict[str, Any]:
    """
    Generate daily study content based on processed files

    Args:
        results: List of processing results
        exam_type: Type of exam
        exam_date: Date of exam

    Returns:
        Dictionary with daily content plan
    """
    try:
        logger.info(f"Generating daily content for {exam_type}")

        # Configure Google Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        genai.configure(api_key=api_key)

        # Initialize model
        model = genai.GenerativeModel("gemini-1.5-pro")

        # Get relevant content from vector database
        with get_db() as db:
            # Create a query to find relevant content for daily study planning
            query = f"Create daily study plan for {exam_type} exam with topics, time allocation, and practice exercises"

            # Search for similar chunks with metadata filter for this exam type
            metadata_filter = {"exam_type": exam_type} if exam_type else None
            relevant_chunks = search_similar_chunks(
                query=query,
                top_k=15,  # Get top 15 most relevant chunks for more comprehensive content
                metadata_filter=metadata_filter,
                db=db
            )

            # Extract content from chunks
            relevant_content = "\n\n".join([chunk["content"] for chunk in relevant_chunks])

            # If no relevant content found in vector DB, fall back to results
            if not relevant_content:
                logger.warning("No relevant content found in vector database, using raw results")
                relevant_content = "\n\n".join([result["extracted_text"] for result in results
                                   if "Error:" not in result["extracted_text"]])
            else:
                logger.info(f"Found {len(relevant_chunks)} relevant chunks in vector database for daily content")

        # Calculate days until exam
        days_until_exam = 90  # Default to 90 days
        try:
            exam_date_obj = datetime.strptime(exam_date, "%Y-%m-%d")
            today = datetime.now()
            days_until_exam = (exam_date_obj - today).days
            if days_until_exam < 1:
                days_until_exam = 90  # Default if date is in the past
        except:
            logger.warning(f"Could not parse exam date: {exam_date}, using default 90 days")

        # Calculate how many batches of 8 days we need to generate
        num_batches = (days_until_exam + 7) // 8  # Ceiling division
        if num_batches < 1:
            num_batches = 1

        # Generate study plans in batches of 8 days
        all_daily_content = {}
        current_date = datetime.now()

        for batch in range(num_batches):
            batch_start_day = batch * 8 + 1
            batch_end_day = min((batch + 1) * 8, days_until_exam)

            # Skip if we've already covered all days
            if batch_start_day > days_until_exam:
                break

            logger.info(f"Generating study plan for days {batch_start_day} to {batch_end_day}")

            # Generate prompt for this batch
            prompt = f"""
            Based on the following educational content, create a daily study plan for a student preparing for the {exam_type} exam.

            Generate a detailed study plan for days {batch_start_day} to {batch_end_day} of the preparation.

            The plan should include:
            1. A breakdown of topics to study each day
            2. Time allocation for each topic (in hours)
            3. Recommended practice exercises
            4. Key concepts to focus on

            DO NOT include any mock tests or practice questions.

            Format the output as a structured JSON with a separate entry for each day, where each day includes:
            - topics: array of topics to study
            - time_allocation: object mapping topics to hours
            - practice: array of recommended exercises
            - key_concepts: array of important concepts to understand

            Content:
            {relevant_content[:8000]}  # Limit content length to avoid token limits
            """

            try:
                response = await asyncio.to_thread(
                    lambda: model.generate_content(prompt)
                )

                # Parse response as JSON
                try:
                    batch_content = json.loads(response.text)

                    # Add dates to each day's plan
                    for day_num in range(batch_start_day, batch_end_day + 1):
                        day_key = f"day_{day_num}"
                        if day_key in batch_content or str(day_num) in batch_content:
                            actual_key = day_key if day_key in batch_content else str(day_num)
                            plan_date = (current_date + timedelta(days=day_num-1)).strftime("%Y-%m-%d")

                            # Add the date to the plan
                            if isinstance(batch_content[actual_key], dict):
                                batch_content[actual_key]["date"] = plan_date
                            else:
                                # If it's not a dict, convert it to one
                                content = batch_content[actual_key]
                                batch_content[actual_key] = {
                                    "content": content,
                                    "date": plan_date
                                }

                    # Add this batch to the overall content
                    all_daily_content.update(batch_content)

                except json.JSONDecodeError:
                    # If not valid JSON, create a structured format
                    for day_num in range(batch_start_day, batch_end_day + 1):
                        day_key = f"day_{day_num}"
                        plan_date = (current_date + timedelta(days=day_num-1)).strftime("%Y-%m-%d")

                        all_daily_content[day_key] = {
                            "content": f"Day {day_num} plan: {response.text}",
                            "date": plan_date
                        }
            except Exception as e:
                logger.error(f"Error generating batch {batch}: {str(e)}")
                # Add error message for this batch
                for day_num in range(batch_start_day, batch_end_day + 1):
                    day_key = f"day_{day_num}"
                    plan_date = (current_date + timedelta(days=day_num-1)).strftime("%Y-%m-%d")

                    all_daily_content[day_key] = {
                        "content": f"Error generating content: {str(e)}",
                        "date": plan_date
                    }

        # Add metadata
        final_content = {
            "exam_type": exam_type,
            "exam_date": exam_date,
            "days_until_exam": days_until_exam,
            "generated_at": datetime.now().isoformat(),
            "daily_plans": all_daily_content
        }

        # Save daily content
        output_folder = os.getenv("OUTPUT_FOLDER", "data/output")
        daily_content_file = os.path.join(output_folder, f"daily_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        with open(daily_content_file, 'w', encoding='utf-8') as f:
            json.dump(final_content, f, ensure_ascii=False, indent=2)

        return final_content
    except Exception as e:
        logger.error(f"Error generating daily content: {str(e)}")
        return {"error": str(e)}

async def get_motivational_quotes() -> List[str]:
    """
    Get motivational quotes for students

    Returns:
        List of motivational quotes
    """
    try:
        logger.info("Getting motivational quotes")

        # Configure Google Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        genai.configure(api_key=api_key)

        # Initialize model
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Generate quotes
        prompt = """
        Generate 10 motivational quotes for students preparing for exams.
        Each quote should be inspiring, concise, and focused on academic success.
        Format the output as a JSON array of strings.
        """

        response = await asyncio.to_thread(
            lambda: model.generate_content(prompt)
        )

        # Parse response as JSON
        try:
            quotes = json.loads(response.text)
        except:
            # If not valid JSON, extract quotes from text
            text = response.text
            lines = text.strip().split('\n')
            quotes = [line.strip() for line in lines if line.strip()]

        return quotes
    except Exception as e:
        logger.error(f"Error getting motivational quotes: {str(e)}")
        return [
            "The harder you work for something, the greater you'll feel when you achieve it.",
            "Success is the sum of small efforts, repeated day in and day out.",
            "Don't wish it were easier; wish you were better.",
            "The expert in anything was once a beginner.",
            "The only way to do great work is to love what you do."
        ]
