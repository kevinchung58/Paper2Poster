# Project TODO List

This document tracks the development tasks for the Interactive Poster Generator project.

## Phase 1: Architecture Refinement and Code Quality (Completed)

-   **[X] 1. Integrate Testing Framework:**
    -   [X] Add `pytest`, `httpx`, `pytest-asyncio`, and other required dependencies to `interactive_poster_backend/requirements.txt`.
    -   [X] Install new dependencies.
    -   [X] Create a basic test file (`interactive_poster_backend/tests/test_main.py`) and ensure the test runner is configured correctly.
-   **[X] 2. Refactor Complex Business Logic:**
    -   [X] Create a new `services` module (`interactive_poster_backend/services/`).
    -   [X] Refactor the complex logic from `poster_router.py:handle_llm_prompt` into a dedicated service function.
    -   [X] Refactor the complex logic from `database/crud.py:update_poster_data` into a dedicated service function.
-   **[X] 3. Clean Up Schema Definitions:**
    -   [X] Remove all commented-out old code and duplicate class definitions in `schemas/models.py`.
    -   [X] Standardize Pydantic model definitions for clarity and consistency.
-   **[X] 4. Fix Frontend Linting Issues:**
    -   [X] Address all `@typescript-eslint/no-explicit-any` errors by providing proper types.
    -   [X] Remove all unused variables (`@typescript-eslint/no-unused-vars`).

## Phase 2: Solidification and DX (Developer Experience)

-   **[ ] 1. Backend Unit Tests:**
    -   [ ] Write comprehensive unit tests for the new `poster_service.py` to cover various update scenarios and ensure business logic is correct.
-   **[ ] 2. Harden System Dependencies:**
    -   [ ] Replace hardcoded strings like `"poster_title"` with enums or constants.
    -   [ ] Add a startup check to verify that the `soffice` command (LibreOffice) is available in the system's PATH.
-   **[ ] 3. Generate Static API Documentation:**
    -   [ ] Create a script to generate a static `openapi.json` file from the running FastAPI application.
    -   [ ] Commit the `openapi.json` to the repository to facilitate easier frontend development.
-   **[ ] 4. Frontend Testing Framework:**
    -   [ ] Add a testing framework (e.g., Vitest) to the `interactive-poster-ui` project.
    -   [ ] Write a simple component test to ensure the framework is set up correctly.
-   **[ ] 5. General Feature Enhancements:**
    -   [ ] Implement more sophisticated error handling and user feedback on the frontend.
    -   [ ] Add user authentication and authorization.
    -   [ ] Enhance the style customization options.

## Phase 3: Strategic Initiatives (Research)

-   **[ ] 1. `presenton` Integration Analysis:**
    -   [ ] Review the `presenton` GitHub repository (`https://github.com/presenton/presenton`).
    -   [ ] Analyze its features, technology stack, and architecture.
    -   [ ] Propose a strategy for how it could be integrated as a platform for this project.
-   **[ ] 2. Docker-less Strategy Evaluation:**
    -   [ ] Analyze the pros and cons of removing the Docker dependency.
    -   [ ] Investigate alternatives for managing the LibreOffice dependency to improve portability and ease of setup.

## Known Issues / Blockers

-   **[ ] Frontend Verification (`Playwright`) Blocked:**
    -   **Symptom:** Playwright tests consistently fail with a `TimeoutError`.
    -   **Root Cause:** The backend server (`uvicorn`) fails to start correctly within the test environment.
    -   **Next Step:** This issue requires an in-depth, isolated debugging session. In the interest of efficiency, this task is currently **skipped**.