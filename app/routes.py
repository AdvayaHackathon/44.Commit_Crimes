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
@app.route('/mock_test')
def mock_test():
    return render_template('mock_test.html')

@app.route('/api/daily-content')
def get_daily_content():
    try:
        # Get the latest JSON file from the output directory
        output_dir = os.path.join('data', 'output')
        json_files = [f for f in os.listdir(output_dir) if f.startswith('daily_content_') and f.endswith('.json')]
        
        if not json_files:
            return jsonify({
                'status': 'error',
                'message': 'No daily content files found'
            }), 404

        # Get the most recent file based on timestamp in filename
        latest_file = max(json_files)
        file_path = os.path.join(output_dir, latest_file)

        with open(file_path, 'r') as f:
            content = json.load(f)

        # Process the content to ensure proper date formatting
        processed_content = {
            'exam_type': content.get('exam_type', 'GATE CSE'),
            'exam_date': content.get('exam_date'),
            'days_until_exam': content.get('days_until_exam', 0),
            'daily_plans': {}
        }

        # Convert the daily plans into a date-indexed format
        if 'daily_plans' in content:
            for day_num, plan in content['daily_plans'].items():
                # Calculate the date for this plan
                if content.get('exam_date'):
                    exam_date = datetime.strptime(content['exam_date'], '%Y-%m-%d')
                    plan_date = exam_date - timedelta(days=int(content['days_until_exam']) - int(day_num))
                    date_str = plan_date.strftime('%Y-%m-%d')
                else:
                    # If no exam date, use today + day_num as date
                    plan_date = datetime.now() + timedelta(days=int(day_num))
                    date_str = plan_date.strftime('%Y-%m-%d')

                processed_content['daily_plans'][date_str] = {
                    'date': date_str,
                    'day_number': day_num,
                    'content': plan.get('content', ''),
                    'topics': plan.get('topics', []),
                    'time_allocation': plan.get('time_allocation', {}),
                    'key_concepts': plan.get('key_concepts', []),
                    'practice_items': plan.get('practice_items', [])
                }

        return jsonify({
            'status': 'success',
            'data': processed_content
        })

    except Exception as e:
        print(f"Error loading daily content: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error loading daily content: {str(e)}'
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

@app.route('/daily-report')
def daily_report():
    return render_template('daily_report.html')

@app.route('/api/daily-report')
def get_daily_report():
    try:
        # Get the latest JSON file from the output directory
        output_dir = os.path.join('data', 'output')
        json_files = [f for f in os.listdir(output_dir) if f.startswith('daily_content_') and f.endswith('.json')]
        
        if not json_files:
            return jsonify({
                'status': 'error',
                'message': 'No daily content files found'
            }), 404

        # Get the most recent file
        latest_file = max(json_files)
        file_path = os.path.join(output_dir, latest_file)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)

        # Process the JSON content
        try:
            daily_plans = {}
            if 'daily_plans' in content:
                for day_num, plan_data in content['daily_plans'].items():
                    # Parse the content string to extract JSON data
                    try:
                        content_str = plan_data.get('content', '')
                        if '```json' in content_str:
                            json_str = content_str.split('```json\n')[1].split('\n```')[0]
                            plan_json = json.loads(json_str)
                        else:
                            plan_json = {}
                    except:
                        plan_json = {}

                    # Calculate the date for this plan
                    if content.get('exam_date'):
                        exam_date = datetime.strptime(content['exam_date'], '%Y-%m-%d')
                        plan_date = exam_date - timedelta(days=int(content['days_until_exam']) - int(day_num))
                    else:
                        plan_date = datetime.now() + timedelta(days=int(day_num))

                    # Extract data from plan_json
                    topics = []
                    time_allocation = {}
                    key_concepts = []
                    practice_items = []

                    for day_data in plan_json.values():
                        if isinstance(day_data, dict):
                            topics.extend(day_data.get('topics', []))
                            if 'time_allocation' in day_data:
                                time_allocation.update(day_data['time_allocation'])
                            key_concepts.extend(day_data.get('key_concepts', []))
                            practice_items.extend(day_data.get('practice_items', []))

                    # Calculate total hours
                    total_hours = sum(float(hours) for hours in time_allocation.values())

                    # Create topics data with percentages
                    topics_data = [
                        {
                            'topic': topic,
                            'hours': float(hours),
                            'percentage': (float(hours) / total_hours * 100) if total_hours > 0 else 0
                        }
                        for topic, hours in time_allocation.items()
                    ]

                    daily_plans[day_num] = {
                        'day_number': day_num,
                        'date': plan_date.strftime('%Y-%m-%d'),
                        'formatted_date': plan_date.strftime('%B %d, %Y'),
                        'topics': topics,
                        'topics_data': topics_data,
                        'total_hours': total_hours,
                        'key_concepts': key_concepts,
                        'practice_items': practice_items,
                        'completion_status': {
                            'topics_covered': len(topics),
                            'concepts_mastered': len(key_concepts),
                            'practice_completed': len(practice_items),
                            'total_study_hours': total_hours
                        }
                    }

            # Calculate overall statistics
            all_plans = list(daily_plans.values())
            total_topics = sum(len(plan['topics']) for plan in all_plans)
            total_concepts = sum(len(plan['key_concepts']) for plan in all_plans)
            total_practice = sum(len(plan['practice_items']) for plan in all_plans)
            total_study_hours = sum(plan['total_hours'] for plan in all_plans)

            report_data = {
                'exam_info': {
                    'exam_type': content.get('exam_type', 'GATE CSE'),
                    'exam_date': content.get('exam_date'),
                    'days_until_exam': content.get('days_until_exam', 0)
                },
                'daily_reports': sorted(all_plans, key=lambda x: x['date']),
                'overall_statistics': {
                    'total_days': len(all_plans),
                    'total_topics': total_topics,
                    'total_concepts': total_concepts,
                    'total_practice_items': total_practice,
                    'total_study_hours': total_study_hours,
                    'average_daily_hours': total_study_hours / len(all_plans) if all_plans else 0
                }
            }

            return jsonify({
                'status': 'success',
                'data': report_data
            })

        except Exception as e:
            print(f"Error processing JSON content: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Error processing JSON content: {str(e)}'
            }), 500

    except Exception as e:
        print(f"Error reading JSON file: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error reading JSON file: {str(e)}'
        }), 500 