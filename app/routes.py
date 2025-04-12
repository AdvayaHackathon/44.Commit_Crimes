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

        with open(file_path, 'r') as f:
            content = json.load(f)

        # Generate daily report data
        report_data = {
            'exam_info': {
                'exam_type': content.get('exam_type', 'GATE CSE'),
                'exam_date': content.get('exam_date'),
                'days_until_exam': content.get('days_until_exam', 0)
            },
            'daily_reports': []
        }

        if 'daily_plans' in content:
            for day_num, plan in content['daily_plans'].items():
                # Calculate the date for this plan
                if content.get('exam_date'):
                    exam_date = datetime.strptime(content['exam_date'], '%Y-%m-%d')
                    plan_date = exam_date - timedelta(days=int(content['days_until_exam']) - int(day_num))
                else:
                    plan_date = datetime.now() + timedelta(days=int(day_num))

                # Extract topics and their time allocations
                topics_data = []
                total_hours = 0
                if isinstance(plan.get('time_allocation'), dict):
                    for topic, hours in plan['time_allocation'].items():
                        try:
                            hours_float = float(hours)
                            total_hours += hours_float
                            topics_data.append({
                                'topic': topic,
                                'hours': hours_float,
                                'percentage': 0  # Will be calculated after total is known
                            })
                        except (ValueError, TypeError):
                            continue

                # Calculate percentages
                for topic_data in topics_data:
                    if total_hours > 0:
                        topic_data['percentage'] = (topic_data['hours'] / total_hours) * 100

                # Create the daily report
                daily_report = {
                    'day_number': day_num,
                    'date': plan_date.strftime('%Y-%m-%d'),
                    'formatted_date': plan_date.strftime('%B %d, %Y'),
                    'topics': plan.get('topics', []),
                    'topics_data': topics_data,
                    'total_hours': total_hours,
                    'key_concepts': plan.get('key_concepts', []),
                    'practice_items': plan.get('practice_items', []),
                    'completion_status': {
                        'topics_covered': len(plan.get('topics', [])),
                        'concepts_mastered': len(plan.get('key_concepts', [])),
                        'practice_completed': len(plan.get('practice_items', [])),
                        'total_study_hours': total_hours
                    }
                }

                report_data['daily_reports'].append(daily_report)

        # Sort daily reports by date
        report_data['daily_reports'].sort(key=lambda x: x['date'])

        # Calculate overall statistics
        total_topics = sum(len(report['topics']) for report in report_data['daily_reports'])
        total_concepts = sum(len(report['key_concepts']) for report in report_data['daily_reports'])
        total_practice = sum(len(report['practice_items']) for report in report_data['daily_reports'])
        total_study_hours = sum(report['total_hours'] for report in report_data['daily_reports'])

        report_data['overall_statistics'] = {
            'total_days': len(report_data['daily_reports']),
            'total_topics': total_topics,
            'total_concepts': total_concepts,
            'total_practice_items': total_practice,
            'total_study_hours': total_study_hours,
            'average_daily_hours': total_study_hours / len(report_data['daily_reports']) if report_data['daily_reports'] else 0
        }

        return jsonify({
            'status': 'success',
            'data': report_data
        })

    except Exception as e:
        print(f"Error generating daily report: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error generating daily report: {str(e)}'
        }), 500 