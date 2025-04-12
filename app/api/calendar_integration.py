import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

async def sync_daily_content_to_calendar(daily_content_file: str) -> Dict[str, Any]:
    """
    Sync daily content from JSON file to calendar
    
    Args:
        daily_content_file: Path to daily content JSON file
        
    Returns:
        Dictionary containing sync status and calendar events
    """
    try:
        # Read daily content file
        with open(daily_content_file, 'r', encoding='utf-8') as f:
            daily_content = json.load(f)
        
        # Extract exam details
        exam_type = daily_content.get('exam_type')
        exam_date = datetime.strptime(daily_content.get('exam_date'), '%Y-%m-%d')
        days_until_exam = daily_content.get('days_until_exam')
        
        # Process daily plans
        calendar_events = []
        daily_plans = daily_content.get('daily_plans', {})
        
        for day_key, plan in daily_plans.items():
            # Extract date and content
            event_date = datetime.strptime(plan.get('date'), '%Y-%m-%d')
            
            # Parse the content JSON string
            content_str = plan.get('content', '')
            if content_str.startswith('Day') and 'plan:' in content_str:
                content_json = content_str.split('plan:', 1)[1].strip()
                try:
                    daily_schedule = json.loads(content_json)
                    
                    # Create calendar event for each day's topics
                    for day_schedule in daily_schedule.values():
                        topics = day_schedule.get('topics', [])
                        time_allocation = day_schedule.get('time_allocation', {})
                        key_concepts = day_schedule.get('key_concepts', [])
                        
                        event = {
                            'date': event_date.strftime('%Y-%m-%d'),
                            'topics': topics,
                            'time_allocation': time_allocation,
                            'key_concepts': key_concepts
                        }
                        calendar_events.append(event)
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing content JSON for {day_key}: {str(e)}")
        
        # Create sync result
        sync_result = {
            'status': 'success',
            'exam_type': exam_type,
            'exam_date': exam_date.strftime('%Y-%m-%d'),
            'days_until_exam': days_until_exam,
            'calendar_events': calendar_events,
            'sync_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Save sync result
        output_folder = os.getenv('OUTPUT_FOLDER', 'data/output')
        os.makedirs(output_folder, exist_ok=True)
        
        output_file = os.path.join(
            output_folder,
            f"calendar_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sync_result, f, ensure_ascii=False, indent=2)
        
        return sync_result
    
    except Exception as e:
        logger.error(f"Error syncing daily content to calendar: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

async def get_calendar_events(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get calendar events for a date range
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        
    Returns:
        Dictionary containing calendar events
    """
    try:
        # Find latest calendar sync file
        output_folder = os.getenv('OUTPUT_FOLDER', 'data/output')
        sync_files = [f for f in os.listdir(output_folder) if f.startswith('calendar_sync_')]
        
        if not sync_files:
            return {
                'status': 'error',
                'message': 'No calendar sync data found'
            }
        
        latest_sync = max(sync_files)
        sync_file = os.path.join(output_folder, latest_sync)
        
        # Read sync data
        with open(sync_file, 'r', encoding='utf-8') as f:
            sync_data = json.load(f)
        
        # Filter events by date range if specified
        events = sync_data.get('calendar_events', [])
        
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            events = [e for e in events if datetime.strptime(e['date'], '%Y-%m-%d') >= start]
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            events = [e for e in events if datetime.strptime(e['date'], '%Y-%m-%d') <= end]
        
        return {
            'status': 'success',
            'exam_type': sync_data.get('exam_type'),
            'exam_date': sync_data.get('exam_date'),
            'days_until_exam': sync_data.get('days_until_exam'),
            'events': events
        }
    
    except Exception as e:
        logger.error(f"Error getting calendar events: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }