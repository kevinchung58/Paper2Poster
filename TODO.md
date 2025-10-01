# Project TODO List

This document tracks the development tasks for the Interactive Poster Generator project.

## Phase 1: Architecture Refinement and Code Quality (Completed)

-   **[X] 1. Integrate Testing Framework:** Established a robust testing foundation for the backend.
-   **[X] 2. Refactor Complex Business Logic:** Migrated business logic to a dedicated service layer.
-   **[X] 3. Clean Up Schema Definitions:** Modernized and clarified all Pydantic data models.
-   **[X] 4. Fix Frontend Linting Issues:** Eliminated all critical linting errors in the React codebase.

## Phase 2: Solidification and DX (Developer Experience) (Completed)

-   **[X] 1. Backend Unit Tests:** Wrote comprehensive unit tests for the new service layer.
-   **[X] 2. Harden System Dependencies:** Removed "magic strings" with enums and added dependency checks.
-   **[X] 3. Generate Static API Documentation:** Created a script to generate a static `openapi.json`.
-   **[X] 4. Frontend Testing Framework:** Successfully integrated Vitest into the frontend project.

## Phase 3: Architectural Transformation: Integrating 'presenton' (Next)

**Strategic Direction:** The project will pivot to use `presenton` (`https://github.com/presenton/presenton`) as the core presentation generation engine. Our current backend (`interactive_poster_backend`) will be transformed into a **Backend for Frontend (BFF)**. Its primary role will be to act as an intermediary between our specialized UI and the powerful, generalized `presenton` API. This avoids reinventing the wheel and allows us to focus on creating a unique, interactive user experience for poster generation.

-   **[ ] 1. Setup `presenton` Instance:**
    -   [ ] Following the `presenton` documentation, set up a local instance using Docker.
    -   [ ] Verify that the `presenton` API is accessible and functional.
-   **[ ] 2. Refactor Backend to Act as BFF:**
    -   [ ] Create a new service/client in our backend to communicate with the `presenton` API.
    -   [ ] Modify `poster_service.py` to translate requests from our UI into API calls to `presenton`'s `/api/v1/ppt/presentation/generate` endpoint.
    -   [ ] Remove our internal PPTX generation logic (`pptx_generator.py`) and the LibreOffice dependency, as this functionality will be fully delegated to `presenton`.
-   **[ ] 3. Adapt Frontend UI:**
    -   [ ] Update the frontend to handle any changes in the API responses from our new BFF.
    -   [ ] Potentially expand the UI to expose some of `presenton`'s more advanced features (e.g., AI template generation from PPTX, wider theme selection).
-   **[ ] 4. Re-evaluate Feature Enhancements:**
    -   [ ] In the context of the new architecture, re-assess the implementation strategy for features like user auth, advanced error handling, and style customization.

## Post-Integration Research

-   **[ ] Docker-less Strategy Evaluation:** Once the integration is complete and stable, investigate the feasibility and trade-offs of running `presenton` without Docker to simplify the local development setup.

## Known Issues / Blockers

-   **[ ] Frontend Verification (`Playwright`) Blocked:**
    -   **Symptom:** Playwright tests consistently fail with a `TimeoutError`.
    -   **Root Cause:** The backend server (`uvicorn`) fails to start correctly within the test environment.
    -   **Next Step:** This issue requires an in-depth, isolated debugging session. It is currently de-prioritized in favor of the strategic pivot to `presenton`.