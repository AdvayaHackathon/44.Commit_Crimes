from typing import Dict, Any, Optional
from datetime import datetime
import json
import os

class CalendarStorage:
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        self.calendar_file = os.path.join(storage_dir, 'calendar_data.json')
        self._initialize_storage()
    
    def _initialize_storage(self) -> None:
        """Initialize the calendar storage if it doesn't exist"""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
        
        if not os.path.exists(self.calendar_file):
            self._save_calendar_data({
                'exam_info': {},
                'daily_schedule': {}
            })
    
    def _load_calendar_data(self) -> Dict[str, Any]:
        """Load calendar data from storage"""
        try:
            with open(self.calendar_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Error loading calendar data: {str(e)}")
    
    def _save_calendar_data(self, data: Dict[str, Any]) -> None:
        """Save calendar data to storage"""
        try:
            with open(self.calendar_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            raise Exception(f"Error saving calendar data: {str(e)}")
    
    def update_exam_info(self, exam_info: Dict[str, Any]) -> None:
        """Update exam information in the calendar"""
        try:
            calendar_data = self._load_calendar_data()
            calendar_data['exam_info'] = exam_info
            self._save_calendar_data(calendar_data)
        except Exception as e:
            raise Exception(f"Error updating exam info: {str(e)}")
    
    def add_daily_schedule(self, date: str, schedule: Dict[str, Any]) -> None:
        """Add or update a daily schedule"""
        try:
            calendar_data = self._load_calendar_data()
            calendar_data['daily_schedule'][date] = schedule
            self._save_calendar_data(calendar_data)
        except Exception as e:
            raise Exception(f"Error adding daily schedule: {str(e)}")
    
    def get_daily_schedule(self, date: str) -> Optional[Dict[str, Any]]:
        """Get schedule for a specific date"""
        try:
            calendar_data = self._load_calendar_data()
            return calendar_data['daily_schedule'].get(date)
        except Exception as e:
            raise Exception(f"Error getting daily schedule: {str(e)}")
    
    def get_exam_info(self) -> Dict[str, Any]:
        """Get exam information"""
        try:
            calendar_data = self._load_calendar_data()
            return calendar_data['exam_info']
        except Exception as e:
            raise Exception(f"Error getting exam info: {str(e)}")