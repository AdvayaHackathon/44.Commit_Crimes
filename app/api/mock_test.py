from fastapi import APIRouter, HTTPException, Request, Body
from typing import List, Dict, Any
import google.generativeai as genai
import os
import json
from datetime import datetime
from pathlib import Path

router = APIRouter(
    prefix="/api/mock-test",
    tags=["mock-test"],
    responses={404: {"description": "Not found"}},
)

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

def generate_prompt(request_data: Dict[str, Any]) -> str:
    """Generate a prompt for the Gemini API based on the request data."""
    return f"""Generate a {request_data['numQuestions']}-question {request_data['difficulty']} level test on {request_data['topic']} in {request_data['subject']}.

Requirements:
1. Mix of multiple choice and subjective questions
2. Each question should be challenging but appropriate for {request_data['difficulty']} level
3. For MCQs, provide 4 options with one correct answer
4. For subjective questions, include a model answer
5. {request_data['instructions'] if request_data['instructions'] else 'Focus on core concepts and their applications'}

Format the response as a JSON object with this structure:
{{
    "questions": [
        {{
            "text": "question text",
            "type": "mcq",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "correct option",
            "explanation": "explanation of the answer"
        }},
        {{
            "text": "question text",
            "type": "subjective",
            "model_answer": "expected answer",
            "rubric": "grading guidelines"
        }}
    ]
}}"""

@router.post("/generate")
async def generate_test(request: Request, data: Dict[str, Any] = Body(...)):
    """Generate a mock test using Gemini API."""
    try:
        # Generate prompt
        prompt = generate_prompt(data)
        
        # Get response from Gemini
        response = model.generate_content(prompt)
        
        # Parse the response
        test_data = json.loads(response.text)
        
        # Process the questions to remove answers before sending to frontend
        processed_questions = []
        for question in test_data['questions']:
            processed_question = {
                'text': question['text'],
                'type': question['type']
            }
            if question['type'] == 'mcq':
                processed_question['options'] = question['options']
            processed_questions.append(processed_question)
        
        return {
            'status': 'success',
            'questions': processed_questions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save")
async def save_test(request: Request, data: Dict[str, Any] = Body(...)):
    """Save the generated test."""
    try:
        # Create output directory if it doesn't exist
        output_dir = Path('data/tests')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_{timestamp}.json"
        
        # Save test data
        with open(output_dir / filename, 'w', encoding='utf-8') as f:
            json.dump(data['test'], f, indent=2, ensure_ascii=False)
        
        return {
            'status': 'success',
            'message': 'Test saved successfully',
            'filename': filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 