from flask import Flask, jsonify, render_template, redirect, send_file
import os
import json
from datetime import datetime, timedelta
from icalendar import Calendar, Event

app = Flask(__name__)

@app.route('/')
def index():
    return redirect('/planner')

@app.route('/planner')
def planner():
    return render_template('planner.html')

@app.route('/api/daily-content')
def get_daily_content():
    try:
        # Read the specific JSON file
        json_path = 'data/output/daily_content_20250412_040702.json'
        
        if not os.path.exists(json_path):
            return jsonify({
                'status': 'error',
                'message': 'Content file not found'
            }), 404

        # Read and parse the JSON content
        with open(json_path, 'r') as f:
            content = json.load(f)
        
        # Process the content to match the calendar format
        processed_content = {
            'exam_type': content.get('exam_type'),
            'exam_date': content.get('exam_date'),
            'days_until_exam': content.get('days_until_exam'),
            'daily_plans': {}
        }

        # Convert the daily plans to a date-based format
        if 'daily_plans' in content:
            for day_key, plan in content['daily_plans'].items():
                # Extract date from the plan
                date_str = plan.get('date', '')  # Format: YYYY-MM-DD
                if date_str:
                    processed_content['daily_plans'][date_str] = {
                        'content': plan.get('content', ''),
                        'date': date_str
                    }

        return jsonify({
            'status': 'success',
            'data': processed_content
        })
    except Exception as e:
        print(f"Error processing content: {str(e)}")  # Debug log
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 

@app.route('/calendar')
def calendar_view():
    return render_template('calendar.html')

@app.route('/api/study_plan')
def get_study_plan():
    # Read the JSON file
    with open('data/output/daily_content_20250412_040702.json', 'r') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/export/ics')
def export_ics():
    # Read the JSON file
    with open('data/output/daily_content_20250412_040702.json', 'r') as f:
        data = json.load(f)
    
    # Create a new calendar
    cal = Calendar()
    cal.add('prodid', '-//Study Plan Calendar//')
    cal.add('version', '2.0')
    
    # Add events for each day
    for day_key, day_data in data['daily_plans'].items():
        event = Event()
        event.add('summary', f"Study Plan: {day_data['content'].split('topics')[1].split(']')[0]}")
        event.add('dtstart', datetime.strptime(day_data['date'], '%Y-%m-%d'))
        event.add('dtend', datetime.strptime(day_data['date'], '%Y-%m-%d') + timedelta(days=1))
        event.add('description', day_data['content'])
        cal.add_component(event)
    
    # Save the calendar to a temporary file
    ics_path = 'data/study_plan.ics'
    with open(ics_path, 'wb') as f:
        f.write(cal.to_ical())
    
    return send_file(ics_path, as_attachment=True, download_name='study_plan.ics') 