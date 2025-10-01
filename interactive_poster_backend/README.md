# Interactive Poster Generator - Backend

This backend service provides the API for the Interactive Poster Generator application. It uses FastAPI and communicates with a Language Model (LLM) via the CAMEL framework to dynamically generate poster content and previews.

## Features

*   Manages poster sessions and state.
    *   **Persistent Storage:** Utilizes a local SQLite database (`posters.db`) to store all poster data, including titles, content, selected themes, section image URLs, and paths to generated files.
*   **Granular Style Customization:** Supports fine-grained style overrides (e.g., specific font sizes, colors for elements like titles, section text, background colors) which are stored as a JSON object (`style_overrides`) alongside the main poster data in the database. These overrides are layered on top of the selected base theme during PPTX generation.
*   Integrates with CAMEL framework for LLM-based content generation.
    *   **PPTX Generation:** Creates PowerPoint files from poster data, applying selected themes, granular style overrides, and embedding images downloaded from URLs provided for each section.
    *   Generates PNG image previews of posters using headless LibreOffice (live preview may not always render web images, but PPTX will attempt to embed them).
*   Provides a RESTful API for frontend interaction.

## Setup and Running

1.  **Prerequisites:**
    *   Python 3.9+
    *   **LibreOffice:** Must be installed on the system for generating image previews of posters.
        *   By default, the application expects the `soffice` command to be available in the system's PATH.
        *   If `soffice` is installed in a custom location, or you need to use a specific executable (e.g., `libreoffice --headless` on some systems, or a versioned command), you can set the `SOFFICE_COMMAND` environment variable to the full path or custom command for the LibreOffice executable. For example:
            *   On Linux/macOS: `export SOFFICE_COMMAND="/opt/libreoffice7.6/program/soffice"`
            *   On Windows (in Command Prompt): `set SOFFICE_COMMAND="C:\Program Files\LibreOffice\program\soffice.exe"`
        *   The backend (specifically `config.py`) reads this environment variable. If not set, it defaults to `"soffice"`.
    *   Access to an LLM configured via the CAMEL framework (default is Gemini 2.0 Flash via DeepInfra - ensure environment variables for CAMEL/DeepInfra are set if needed by that framework).

2.  **Installation:**
    *   Clone the repository (if applicable).
    *   Navigate to the `interactive_poster_backend` directory.
    *   Create a Python virtual environment (recommended):
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows: venv\Scripts\activate
        ```
    *   Install dependencies:
        ```bash
        pip install -r requirements.txt
        ```

3.  **Running the Backend:**
    *   From the `interactive_poster_backend` directory (or its parent, adjusting the module path):
        ```bash
        uvicorn main:app --reload --port 8000
        ```
    *   The API will be available at `http://localhost:8000`.
    *   Interactive API documentation (Swagger UI) will be at `http://localhost:8000/docs`.
    *   Alternative API documentation (ReDoc) will be at `http://localhost:8000/redoc`.

## Data Storage

Upon first run (or if the file is deleted), a `posters.db` SQLite database file will be automatically created in the main `interactive_poster_backend` directory (alongside `main.py`). This file contains all poster session data, including titles, content, and paths to generated files.

## API Overview

The API provides endpoints for:
*   Creating and managing poster sessions.
*   Sending prompts to the LLM for content generation/modification.
*   Retrieving poster data and image previews.
*   Generating and downloading final PPTX files.
*   The `/api/v1/posters/{poster_id}/prompt` endpoint is the primary interface for content modification. It can:
    *   Send natural language prompts to the LLM for content generation or changes, targeting specific elements (via `target_element_id`) or the poster generally.
    *   Accept direct text updates for specific elements by setting an `is_direct_update: true` flag in the request body, where `prompt_text` then serves as the exact new content, bypassing the LLM.
    *   Process updates to the poster's `selected_theme` and granular `style_overrides`.
*   For full request and response schema details, please refer to the auto-generated API documentation available at `/docs` or `/redoc` when the server is running.


## Temporary Files and Cleanup

*   The application uses dedicated directories for temporary files:
    *   `temp_posters/`: Stores generated PPTX files.
    *   `temp_previews/`: Stores generated PNG preview images.
*   These directories are located at the root of the backend application module (e.g., within `interactive_poster_backend/`) and are created automatically if they don't exist at application startup. All paths used for these temporary files are absolute, ensuring consistent behavior regardless of where the application is launched from.
*   **Automatic Cleanup:** A cleanup process runs automatically each time the application starts. This process deletes files from both `temp_posters/` and `temp_previews/` that are older than a configured number of days (default is 7 days, as set in `config.py:DAYS_TO_KEEP_TEMP_FILES`). This helps manage disk space over time. Details of the cleanup process (number of files deleted, any errors encountered) are logged to the console.

## Dependencies

*   FastAPI: Web framework.
*   Uvicorn: ASGI server.
*   Pydantic: Data validation.
*   python-pptx: For generating PowerPoint files.
*   SQLAlchemy: For Object-Relational Mapping (ORM) interaction with the SQLite database.
*   requests: For downloading images from URLs during PPTX generation.
*   CAMEL framework (and its dependencies for LLM interaction).
*   (Implicit) LibreOffice for `soffice`.
