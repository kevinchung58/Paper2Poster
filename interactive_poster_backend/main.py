from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# import os # No longer needed here for dir creation if done in config or on_event

# Import the configuration
from . import config
from .routers import poster_router
from .utils import cleanup
from .database import database_setup
import logging
import os # Added for os.makedirs

# Configure logging for main application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- Application Setup ---
app = FastAPI(
    title="Interactive Poster Generator API",
    description="API for creating and managing interactive scientific posters.",
    version="0.1.0"
)

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup: Ensuring temporary directories exist...")
    config.create_temp_dirs() # Creates temp_posters and temp_previews

    # Ensure uploaded images directory exists
    try:
        os.makedirs(config.UPLOADED_IMAGES_DIR, exist_ok=True)
        logger.info(f"Ensured uploaded images directory exists: {config.UPLOADED_IMAGES_DIR}")
    except Exception as e:
        logger.error(f"Could not create uploaded images directory {config.UPLOADED_IMAGES_DIR}: {e}", exc_info=True)

    logger.info("Application startup: Initializing database and creating tables...")
    try:
        database_setup.create_db_and_tables()
        logger.info("Database tables checked/created successfully.")
    except Exception as e:
        logger.error(f"Error during database setup: {e}", exc_info=True)

    logger.info("Application startup: Performing initial cleanup of temporary files...")
    try:
        cleanup.cleanup_old_files(config.TEMP_POSTERS_DIR, config.DAYS_TO_KEEP_TEMP_FILES)
        cleanup.cleanup_old_files(config.TEMP_PREVIEWS_DIR, config.DAYS_TO_KEEP_TEMP_FILES)
        # Not cleaning up UPLOADED_IMAGES_DIR with the same date-based policy yet,
        # as their lifecycle might be different (e.g., keep as long as referenced by a poster).
        # A more sophisticated cleanup for uploaded_images would be needed if it grows indefinitely.
        logger.info("Temporary file cleanup finished successfully.")
    except Exception as e:
        logger.error(f"Error during startup cleanup: {e}", exc_info=True)

# --- CORS Configuration ---
# Define the list of origins that should be allowed to make cross-origin requests.
# For development, this typically includes your frontend development server's address.
# For production, you would replace/add your production frontend's URL.
origins = [
    "http://localhost:5173",    # Default Vite React app port
    "http://127.0.0.1:5173",   # Also common for local development
    # "https://your-production-frontend.com", # Example for production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # List of origins that are allowed to make requests.
    allow_credentials=True,     # Whether to support cookies for cross-origin requests.
    allow_methods=["*"],        # A list of HTTP methods that are allowed. Use ["GET", "POST"] for stricter control.
    allow_headers=["*"],        # A list of HTTP request headers that are supported.
)

# --- API Routers ---
# Include the router for poster-related endpoints.
app.include_router(poster_router.router, prefix="/api/v1", tags=["Posters API"])

# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint for the API.
    Provides a welcome message and basic API information.
    """
    return {
        "message": "Welcome to the Interactive Poster Generator API!",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

# --- Temp Directory Creation (Optional: on-demand in routers is also fine) ---
# It's often better to ensure directories are created when they are first needed
# within the specific functions/endpoints that use them, to avoid issues if the
# main.py module isn't reloaded but the directories get deleted.
# However, creating them at startup is also a common pattern.

# TEMP_POSTERS_DIR = "temp_posters"
# TEMP_PREVIEWS_DIR = "temp_previews" # Defined in config now

# @app.on_event("startup") # This is now implemented above
# async def startup_event():
#     config.create_temp_dirs()

# To run the app (if this file is named main.py):
# uvicorn main:app --reload --port 8000
# Or from a directory above:
# uvicorn interactive_poster_backend.main:app --reload --port 8000
