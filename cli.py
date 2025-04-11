#!/usr/bin/env python3
"""
CLI tool for Educational Content Analysis System
"""

import os
import sys
import argparse
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add app to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import app modules
from app.core.ocr.processor import process_file
from app.core.analysis.text_analyzer import analyze_text
from app.core.planner.test_planner import generate_test_plan, generate_learning_outcome_sheet

async def process_folder(input_folder: str, recursive: bool = False) -> List[Dict[str, Any]]:
    """
    Process all files in a folder
    
    Args:
        input_folder: Path to input folder
        recursive: Whether to process subfolders recursively
        
    Returns:
        List of processing results
    """
    logger.info(f"Processing folder: {input_folder}")
    
    # Check if folder exists
    if not os.path.isdir(input_folder):
        logger.error(f"Folder not found: {input_folder}")
        return []
    
    # Get all files
    files = []
    if recursive:
        for root, _, filenames in os.walk(input_folder):
            for filename in filenames:
                files.append(os.path.join(root, filename))
    else:
        files = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]
    
    # Filter files by extension
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    files = [f for f in files if Path(f).suffix.lower() in valid_extensions]
    
    logger.info(f"Found {len(files)} files to process")
    
    # Process files
    results = []
    failed_files = []
    
    for file_path in files:
        try:
            logger.info(f"Processing file: {file_path}")
            
            # Process file with OCR
            ocr_result = await process_file(file_path)
            
            # Analyze text
            analysis_result = await analyze_text(
                text=ocr_result["full_text"],
                language=ocr_result["language"],
                file_type=ocr_result["file_type"]
            )
            
            results.append({
                "file_path": file_path,
                "ocr_result": ocr_result,
                "analysis_result": analysis_result
            })
            
            logger.info(f"Successfully processed file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {str(e)}")
            failed_files.append({"file_path": file_path, "error": str(e)})
    
    # Log failed files
    if failed_files:
        logger.warning(f"Failed to process {len(failed_files)} files")
        
        # Save failed files to JSON
        output_folder = os.getenv("OUTPUT_FOLDER", "data/output")
        os.makedirs(output_folder, exist_ok=True)
        
        failed_file_path = os.path.join(output_folder, "failed_files.json")
        
        with open(failed_file_path, 'w', encoding='utf-8') as f:
            json.dump(failed_files, f, ensure_ascii=False, indent=2)
    
    return results

async def generate_plans(analysis_results: List[Dict[str, Any]], test_types: List[str]) -> None:
    """
    Generate test plans for analysis results
    
    Args:
        analysis_results: List of analysis results
        test_types: List of test types to generate
    """
    logger.info(f"Generating test plans for {len(analysis_results)} analysis results")
    
    # Extract analysis results
    extracted_results = [result["analysis_result"] for result in analysis_results]
    
    # Generate test plans for each type
    for test_type in test_types:
        logger.info(f"Generating {test_type} test plan")
        
        try:
            plan = await generate_test_plan(
                analysis_results=extracted_results,
                test_type=test_type,
                duration=60,  # Default duration
                total_marks=100  # Default total marks
            )
            
            logger.info(f"Successfully generated {test_type} test plan with {plan['question_count']} questions")
        except Exception as e:
            logger.error(f"Failed to generate {test_type} test plan: {str(e)}")
    
    # Generate learning outcome sheet
    try:
        logger.info("Generating learning outcome sheet")
        
        outcome_sheet = await generate_learning_outcome_sheet(
            analysis_results=extracted_results,
            days=7  # Default days
        )
        
        logger.info(f"Successfully generated learning outcome sheet for {len(outcome_sheet['topics'])} topics")
    except Exception as e:
        logger.error(f"Failed to generate learning outcome sheet: {str(e)}")

def main():
    """
    Main CLI function
    """
    parser = argparse.ArgumentParser(description='Educational Content Analysis System CLI')
    
    parser.add_argument('--input', '-i', type=str, required=True,
                        help='Input folder containing files to process')
    
    parser.add_argument('--recursive', '-r', action='store_true',
                        help='Process subfolders recursively')
    
    parser.add_argument('--test-types', '-t', type=str, nargs='+',
                        default=['mixed', 'objective', 'subjective', 'practical'],
                        help='Test types to generate (mixed, objective, subjective, practical)')
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ.setdefault("INPUT_FOLDER", "data/input")
    os.environ.setdefault("PROCESSED_FOLDER", "data/processed")
    os.environ.setdefault("OUTPUT_FOLDER", "data/output")
    
    # Run async functions
    async def run():
        # Process folder
        results = await process_folder(args.input, args.recursive)
        
        if results:
            # Generate test plans
            await generate_plans(results, args.test_types)
            
            logger.info("Processing completed successfully")
        else:
            logger.warning("No files were processed")
    
    asyncio.run(run())

if __name__ == "__main__":
    main()
