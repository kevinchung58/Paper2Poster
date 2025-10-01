# Project TODO List

This document tracks the development tasks for the Interactive Poster Generator project.

## Phase 1: Architecture Refinement and Code Quality

### Backend
-   **[X] 1. Integrate Testing Framework:**
    -   [X] Add `pytest`, `httpx`, `pytest-asyncio`, and other required dependencies to `interactive_poster_backend/requirements.txt`.
    -   [X] Install new dependencies.
    -   [X] Create a basic test file (`interactive_poster_backend/tests/test_main.py`) and ensure the test runner is configured correctly.
-   **[X] 2. Refactor Complex Business Logic:**
    -   [X] Create a new `services` module (`interactive_poster_backend/services/`).
    -   [X] Refactor the complex logic from `poster_router.py:handle_llm_prompt` into a dedicated service function.
    -   [X] Refactor the complex logic from `database/crud.py:update_poster_data` into a dedicated service function.
    -   [ ] Write unit tests for the new service functions to cover various update scenarios.
-   **[X] 3. Clean Up Schema Definitions:**
    -   [X] Remove all commented-out old code and duplicate class definitions in `schemas/models.py`.
    -   [X] Standardize Pydantic model definitions for clarity and consistency.
-   **[ ] 4. Harden System Dependencies:**
    -   [ ] Replace hardcoded strings like `"poster_title"` with enums or constants.
    -   [ ] Add a startup check to verify that the `soffice` command (LibreOffice) is available in the system's PATH.
-   **[ ] 5. Generate Static API Documentation:**
    -   [ ] Create a script to generate a static `openapi.json` file from the running FastAPI application.
    -   [ ] Commit the `openapi.json` to the repository to facilitate easier frontend development.

### Frontend
-   **[X] 1. Fix Linting Issues:**
    -   [X] Address all `@typescript-eslint/no-explicit-any` errors by providing proper types.
    -   [X] Remove all unused variables (`@typescript-eslint/no-unused-vars`).
-   **[ ] 2. Integrate Testing Framework:**
    -   [ ] Add a testing framework (e.g., Vitest) to the `interactive-poster-ui` project.
    -   [ ] Write a simple component test to ensure the framework is set up correctly.

## Phase 2: Feature Enhancements (Future)

-   **[ ]** Implement more sophisticated error handling and user feedback on the frontend.
-   **[ ]** Explore replacing the LibreOffice dependency with a library-based solution for preview generation to improve portability.
-   **[ ]** Add user authentication and authorization.
-   **[ ]** Enhance the style customization options.

## Known Issues / Blockers

-   **[ ] Frontend Verification (`Playwright`) Blocked:**
    -   **Symptom:** Playwright tests consistently fail with a `TimeoutError` while waiting for the "Start New Poster" button to appear.
    -   **Root Cause:** The backend server (`uvicorn`) fails to start correctly within the test environment, even though the process appears to be running. It seems to be a "zombie" process that cannot handle requests, likely due to a silent `ImportError` that occurs before the application's logger is fully initialized.
    -   **Attempts:**
        -   Restarting servers individually and together.
        -   Correcting the `uvicorn` startup command to be run from the project root.
        -   Separating `stdout` and `stderr` to capture underlying startup errors.
    -   **Next Step:** This issue requires a more in-depth, isolated debugging session. In the interest of efficiency, this task is currently **skipped** to allow for the submission of other completed work.