from pathlib import Path
import os

# APP_ROOT_DIR will be the 'interactive_poster_backend' directory
APP_ROOT_DIR = Path(__file__).resolve().parent

TEMP_POSTERS_DIR = APP_ROOT_DIR / "temp_posters"
TEMP_PREVIEWS_DIR = APP_ROOT_DIR / "temp_previews"

def create_temp_dirs():
    """Creates the temporary directories if they don't exist."""
    os.makedirs(TEMP_POSTERS_DIR, exist_ok=True)
    print(f"Ensured directory exists: {TEMP_POSTERS_DIR}")
    os.makedirs(TEMP_PREVIEWS_DIR, exist_ok=True)
    print(f"Ensured directory exists: {TEMP_PREVIEWS_DIR}")

# --- Database Configuration ---
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db" # Example for PostgreSQL
SQLITE_DB_FILE = APP_ROOT_DIR / "posters.db" # Defines the SQLite file in the application root
SQLALCHEMY_DATABASE_URL = f"sqlite:///{SQLITE_DB_FILE.resolve()}" # Absolute path for SQLite connection

# --- LibreOffice soffice Command Configuration ---
# Users can set the SOFFICE_COMMAND environment variable if 'soffice'
# is not in their system PATH or if they need to use a specific version/path.
SOFFICE_COMMAND = os.getenv("SOFFICE_COMMAND", "soffice")

# --- Temporary File Cleanup Configuration ---
DAYS_TO_KEEP_TEMP_FILES = 7 # Number of days to keep temporary files

# --- Configuration for Uploaded Images ---
UPLOADED_IMAGES_DIR_NAME = "uploaded_images" # Name of the directory
UPLOADED_IMAGES_DIR = APP_ROOT_DIR / UPLOADED_IMAGES_DIR_NAME # Absolute path

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif"} # Set of allowed extensions
MAX_IMAGE_UPLOAD_SIZE_MB = 5 # Max image upload size in Megabytes

# Example of how to get a path for a file in temp_posters
# def get_poster_pptx_path(poster_id: str) -> Path:
#     return TEMP_POSTERS_DIR / f"{poster_id}.pptx"

# def get_poster_preview_path(poster_id: str, base_pptx_filename: str) -> Path:
#     # Assuming preview is named after the pptx file
#     preview_filename = Path(base_pptx_filename).stem + ".png"
#     return TEMP_PREVIEWS_DIR / preview_filename
