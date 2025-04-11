import os
import json
import random
from typing import Dict, Any, List, Optional
import logging
import pandas as pd
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_test_plan(
    analysis_results: List[Dict[str, Any]],
    test_type: str = "mixed",
    duration: int = 60,  # minutes
    total_marks: int = 100
) -> Dict[str, Any]:
    """
    Generate a test plan based on analyzed content
    
    Args:
        analysis_results: List of analysis results
        test_type: Type of test (objective, subjective, practical, or mixed)
        duration: Duration of the test in minutes
        total_marks: Total marks for the test
        
    Returns:
        Dictionary containing the test plan
    """
    try:
        # Extract all questions from analysis results
        all_questions = []
        topics = set()
        
        for result in analysis_results:
            categorized = result.get("categorized_questions", {})
            
            # Add questions based on test type
            if test_type == "objective":
                all_questions.extend(categorized.get("objective", []))
            elif test_type == "subjective":
                all_questions.extend(categorized.get("subjective", []))
            elif test_type == "practical":
                all_questions.extend(categorized.get("practical", []))
            else:  # mixed
                all_questions.extend(categorized.get("objective", []))
                all_questions.extend(categorized.get("subjective", []))
                all_questions.extend(categorized.get("practical", []))
            
            # Collect topics
            topics.update(result.get("topics", []))
        
        # Calculate time per mark
        time_per_mark = duration / total_marks
        
        # Select questions to meet total marks
        selected_questions = []
        current_marks = 0
        
        # Sort questions by marks (ascending)
        sorted_questions = sorted(all_questions, key=lambda q: q["marks"])
        
        while current_marks < total_marks and sorted_questions:
            # Find a question that fits within remaining marks
            for i, question in enumerate(sorted_questions):
                if current_marks + question["marks"] <= total_marks:
                    selected_questions.append(question)
                    current_marks += question["marks"]
                    sorted_questions.pop(i)
                    break
            else:
                # If no question fits, break the loop
                break
        
        # Calculate distribution by question type
        question_types = {"objective": 0, "subjective": 0, "practical": 0}
        
        for result in analysis_results:
            categorized = result.get("categorized_questions", {})
            
            for q_type in question_types:
                for question in categorized.get(q_type, []):
                    if question in selected_questions:
                        question_types[q_type] += question["marks"]
        
        # Calculate percentages
        for q_type in question_types:
            question_types[q_type] = {
                "marks": question_types[q_type],
                "percentage": round((question_types[q_type] / current_marks) * 100, 2) if current_marks > 0 else 0
            }
        
        # Create test plan
        test_plan = {
            "test_type": test_type,
            "duration": duration,
            "total_marks": current_marks,
            "question_count": len(selected_questions),
            "questions": selected_questions,
            "distribution": question_types,
            "topics": list(topics),
            "estimated_time_per_mark": time_per_mark
        }
        
        # Save test plan
        output_folder = os.getenv("OUTPUT_FOLDER", "data/output")
        os.makedirs(output_folder, exist_ok=True)
        
        output_file = os.path.join(
            output_folder,
            f"test_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_plan, f, ensure_ascii=False, indent=2)
        
        return test_plan
    except Exception as e:
        logger.error(f"Error generating test plan: {str(e)}")
        raise

async def generate_learning_outcome_sheet(
    analysis_results: List[Dict[str, Any]],
    days: int = 7
) -> Dict[str, Any]:
    """
    Generate a day-wise learning outcome sheet
    
    Args:
        analysis_results: List of analysis results
        days: Number of days to plan for
        
    Returns:
        Dictionary containing the learning outcome sheet
    """
    try:
        # Extract topics from analysis results
        all_topics = set()
        for result in analysis_results:
            all_topics.update(result.get("topics", []))
        
        # Convert to list and sort
        topics_list = sorted(list(all_topics))
        
        # Generate random mastery levels for each topic for each day
        # In a real application, this would be based on actual student performance
        learning_outcomes = {}
        
        start_date = datetime.now()
        
        for i in range(days):
            date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            
            daily_outcomes = {}
            for topic in topics_list:
                # Simulate increasing mastery over time
                base_mastery = random.uniform(0.3, 0.5)
                growth_factor = i / days
                mastery = min(0.95, base_mastery + (growth_factor * 0.5))
                
                daily_outcomes[topic] = round(mastery, 2)
            
            learning_outcomes[date] = daily_outcomes
        
        # Create learning outcome sheet
        outcome_sheet = {
            "topics": topics_list,
            "days": days,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": (start_date + timedelta(days=days-1)).strftime("%Y-%m-%d"),
            "outcomes": learning_outcomes
        }
        
        # Save learning outcome sheet
        output_folder = os.getenv("OUTPUT_FOLDER", "data/output")
        os.makedirs(output_folder, exist_ok=True)
        
        output_file = os.path.join(
            output_folder,
            f"learning_outcomes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(outcome_sheet, f, ensure_ascii=False, indent=2)
        
        return outcome_sheet
    except Exception as e:
        logger.error(f"Error generating learning outcome sheet: {str(e)}")
        raise
