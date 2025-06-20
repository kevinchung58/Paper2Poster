# Interactive Poster Generator

This project allows users to interactively generate posters with the assistance of a Large Language Model (LLM). It consists of a Python FastAPI backend and a React frontend.

## Project Structure

*   `interactive_poster_backend/`: Contains the FastAPI backend server, LLM integration (via CAMEL), PPTX generation, and image preview logic. See its own README.md for more details.
*   `interactive-poster-ui/`: Contains the React (Vite + TypeScript) frontend application. See its own README.md for more details.
*   `start_backend.bat`: A Windows batch file to easily start the backend server.
*   `start_frontend.bat`: A Windows batch file to easily start the frontend development server.

## Quick Start (Windows using Batch Files)

1.  **Prerequisites:**
    *   Ensure Python (for backend) and Node.js (for frontend) are installed.
    *   Ensure LibreOffice is installed and `soffice` is in your system's PATH for the backend's image preview feature to work.
    *   Install backend dependencies: Navigate to `interactive_poster_backend/`, set up a virtual environment (e.g., `venv`), activate it, and run `pip install -r requirements.txt`.
    *   Install frontend dependencies: Navigate to `interactive-poster-ui/` and run `npm install` or `yarn install`.

2.  **Run the Application:**
    *   From this project root directory, double-click `start_backend.bat` to launch the backend server. A command prompt window will open.
    *   From this project root directory, double-click `start_frontend.bat` to launch the frontend development server. Another command prompt window will open, and it should also open the UI in your default web browser.

For more detailed setup and information, please refer to the README files within the `interactive_poster_backend` and `interactive-poster-ui` directories.
