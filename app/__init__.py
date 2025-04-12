# Educational Content Analysis and Planning System
# Version: 0.1.0

from flask import Flask, send_from_directory, jsonify
import os
import glob
import json
from datetime import datetime

def create_app():
    app = Flask(__name__)
    
    @app.route('/api/daily-content')
    def get_daily_content():
        try:
            # Get the absolute path to the data/output directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(base_dir, 'data', 'output')
            print(f"Looking for files in: {output_dir}")  # Debug print
            
            # Get all daily content files
            pattern = os.path.join(output_dir, 'daily_content_*.json')
            matching_files = glob.glob(pattern)
            print(f"Found files: {matching_files}")  # Debug print
            
            if not matching_files:
                return jsonify({'error': 'No content found'}), 404
            
            # Get the most recent file
            latest_file = max(matching_files, key=os.path.getctime)
            print(f"Latest file: {latest_file}")  # Debug print
            
            # Read the JSON content
            with open(latest_file, 'r', encoding='utf-8') as f:
                try:
                    content = json.load(f)
                    # Add metadata about the file
                    content['source_file'] = os.path.basename(latest_file)
                    return jsonify({
                        'status': 'success',
                        'data': content,
                        'file_info': {
                            'name': os.path.basename(latest_file),
                            'created': datetime.fromtimestamp(os.path.getctime(latest_file)).isoformat(),
                            'path': latest_file
                        }
                    })
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")  # Debug print
                    return jsonify({'error': 'Invalid JSON content'}), 500
                
        except Exception as e:
            print(f"Error in get_daily_content: {str(e)}")  # Debug logging
            return jsonify({'error': str(e)}), 500

    @app.route('/output/<path:filename>')
    def serve_output_file(filename):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, 'data', 'output')
        return send_from_directory(output_dir, filename)

    return app

# Create the Flask application instance
app = create_app()

from app import routes

if __name__ == '__main__':
    app.run(debug=True)
