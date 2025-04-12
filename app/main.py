import os
import uvicorn
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.api import planner, mock_test
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Run database migrations
try:
    from app.core.migrations.add_pgvector import run_migrations
    if run_migrations():
        logger.info("Database migrations completed successfully")
    else:
        logger.warning("Database migrations failed, some features may not work properly")
except Exception as e:
    logger.error(f"Error running database migrations: {str(e)}")

# Create FastAPI app
app = FastAPI(
    title="Educational Content Analysis System",
    description="AI-powered system for analyzing educational content and generating test plans",
    version="0.1.0",
)

# Import background tasks
from app.core.tasks import start_background_tasks

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="app/templates")

# Import routers
from app.api.upload import router as upload_router
from app.api.analysis import router as analysis_router
from app.api.folder_upload import router as folder_router
from app.api.maintenance import router as maintenance_router

# Include routers
app.include_router(upload_router)
app.include_router(analysis_router)
app.include_router(planner.router)
app.include_router(folder_router)
app.include_router(maintenance_router)
app.include_router(mock_test.router)

# Page routes
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/test-viewer")
async def test_viewer(request: Request):
    return templates.TemplateResponse("test_viewer.html", {"request": request})

@app.get("/planner")
async def planner_page(request: Request):
    return templates.TemplateResponse("planner.html", {"request": request})

@app.get("/daily-report")
async def daily_report(request: Request):
    return templates.TemplateResponse("daily_report.html", {"request": request})

@app.get("/folder-upload")
async def folder_upload(request: Request):
    return templates.TemplateResponse("folder_upload.html", {"request": request})

@app.get("/mock-test")
async def mock_test_page(request: Request):
    return templates.TemplateResponse("mock_test.html", {"request": request})

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Startup event handler
@app.on_event("startup")
async def startup_event():
    logger.info("Starting background tasks")
    start_background_tasks()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
