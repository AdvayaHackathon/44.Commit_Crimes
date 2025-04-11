# User Registration and Dashboard

A Flask application with user registration, login, and a personalized dashboard. The application uses PostgreSQL with pgvector for the database and Google's Material Design Lite for the frontend.

## Features

- User registration and authentication
- Secure password hashing
- User dashboard with profile information
- Responsive design using Google's Material Design Lite

## Prerequisites

- Python 3.8+
- PostgreSQL 12+ (pgvector extension is optional)
- pip (Python package manager)

If you don't have PostgreSQL installed, you can run the following script to get installation instructions:
```
python install_postgres.py
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Run the setup script to create a virtual environment and install dependencies:
   ```
   python setup.py
   ```
   This script will create a virtual environment and install all required packages.

3. Activate the virtual environment:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Check if pgvector is available in your PostgreSQL installation:
   ```
   python check_pgvector.py
   ```
   This script will check if the pgvector extension is available and provide installation instructions if needed.

5. Set up the environment variables and database:
   - Make sure PostgreSQL is running
   - Run the environment setup script:
     ```
     python setup_env.py
     ```
   - Run the database initialization script:
     ```
     python init_db.py
     ```

   Note: All scripts will prompt you for your PostgreSQL credentials

6. Run the application:
   ```
   python app.py
   ```

7. Open your browser and navigate to `http://127.0.0.1:5000`

## Project Structure

- `app.py`: Main application file
- `setup.py`: Project setup script (creates virtual environment and installs dependencies)
- `install_postgres.py`: Script with PostgreSQL installation instructions
- `check_pgvector.py`: Script to check PostgreSQL connection and pgvector availability
- `setup_env.py`: Script to set up environment variables
- `init_db.py`: Database initialization script
- `requirements.txt`: Required Python packages
- `.env`: Environment variables
- `templates/`: HTML templates
  - `base.html`: Base template with common layout
  - `index.html`: Home page
  - `login.html`: Login page
  - `register.html`: Registration page
  - `dashboard.html`: User dashboard
- `static/`: Static files
  - `css/style.css`: Custom CSS styles

## Technologies Used

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Database**: PostgreSQL with pgvector extension
- **Frontend**: HTML, CSS, Google's Material Design Lite
- **Authentication**: Werkzeug security for password hashing
