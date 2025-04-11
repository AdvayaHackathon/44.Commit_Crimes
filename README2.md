# Educational Content Analysis and Planning System

An AI-powered system for analyzing educational content from PDFs/images, generating structured test plans, and providing interactive, multilingual, and visual outputs tailored to students and educators.

## Features

- **OCR Processing**: Extract text from PDFs and images (including handwritten content)
- **Text Analysis**: Extract keywords, questions, marks distribution, and topics
- **Test Planning**: Generate test plans based on content analysis
- **Interactive Web UI**: Dashboard with upload, analysis, and planning features
- **Multilingual Support**: Process content in multiple languages
- **Deployment-Ready**: Docker containerization for easy deployment

## Project Structure

```
Hackathon/
├── app/                      # Main application code
│   ├── api/                  # API endpoints
│   ├── core/                 # Core functionality
│   │   ├── ocr/              # OCR processing
│   │   ├── analysis/         # Text analysis
│   │   ├── planner/          # Test planning
│   │   └── multilingual/     # Language support
│   ├── models/               # Data models
│   ├── static/               # Static files (CSS, JS)
│   └── templates/            # HTML templates
├── config/                   # Configuration files
├── data/                     # Data storage
│   ├── input/                # Input files
│   ├── processed/            # Processed files
│   └── output/               # Output files
├── tests/                    # Unit tests
├── docker/                   # Docker configuration
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables example
├── Dockerfile                # Docker configuration
├── docker-compose.yml        # Docker compose configuration
└── README.md                 # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.9+
- Docker (optional, for containerized deployment)
- Google Cloud account (for OCR and Translation APIs)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd Hackathon
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run the application:
   ```
   python -m app.main
   ```

### Docker Deployment

1. Build the Docker image:
   ```
   docker build -t edu-content-analysis .
   ```

2. Run the container:
   ```
   docker run -p 8000:8000 edu-content-analysis
   ```

Or using Docker Compose:
```
docker-compose up
```

## Usage

1. Access the web interface at `http://localhost:8000`
2. Upload PDF/image files containing educational content
3. View the extracted text and analysis
4. Generate test plans and reports
5. Export results in various formats

## API Documentation

API documentation is available at `http://localhost:8000/docs` when the application is running.

## License

[MIT License](LICENSE)
