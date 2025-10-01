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

**Strategic Direction:** The project will pivot to use `presenton` (`https://github.com/presenton/presenton`) as the core presentation generation engine. Our current backend (`interactive_poster_backend`) will be transformed into a **Backend for Frontend (BFF)**. Its primary role will be to act as an intermediary between our specialized UI and the powerful, generalized `presenton` API.

-   **[ ] 1. Manual `presenton` Setup (Docker-less):**
    -   **[ ] System Dependencies:** Install `python3.11`, `nodejs-20`, `npm`, `nginx`, `libreoffice`, `chromium`, and `ollama` using system package managers.
    -   **[ ] Python Dependencies:** Install all Python packages listed in `Dockerfile.dev` using `pip`.
    -   **[ ] Node.js Dependencies:** Navigate to `servers/nextjs` within the `presenton` codebase and run `npm install`.
    -   **[ ] Nginx Configuration:** Copy the `nginx.conf` file to the system's Nginx configuration directory (e.g., `/etc/nginx/nginx.conf`).
    -   **[ ] Service Activation:** Sequentially start all required services (Nginx, Ollama, FastAPI, MCP, Next.js) using the commands identified in `start.js`.
-   **[ ] 2. Refactor Backend to Act as BFF:**
    -   [ ] Create a new service/client in our backend to communicate with the now locally running `presenton` API (at `http://localhost:5000`).
    -   [ ] Modify `poster_service.py` to translate requests from our UI into API calls to `presenton`.
    -   [ ] Remove our internal PPTX generation logic and the LibreOffice dependency.
-   **[ ] 3. Adapt Frontend UI:**
    -   [ ] Update the frontend to handle any changes in the API responses from our new BFF.
    -   [ ] Potentially expand the UI to expose some of `presenton`'s more advanced features.

## Known Issues / Blockers

-   **[CRITICAL] Disk Space Limitation:**
    -   **Symptom:** `docker pull` command fails with `no space left on device`.
    -   **Impact:** This **blocks** the official, Docker-based setup of `presenton`. The current plan is to mitigate this by performing a manual, "Docker-less" installation.
-   **[ ] Frontend Verification (`Playwright`) Blocked:**
    -   **Symptom:** Playwright tests consistently fail with a `TimeoutError`.
    -   **Root Cause:** The backend server (`uvicorn`) fails to start correctly within the test environment.
    -   **Next Step:** This issue is currently de-prioritized in favor of the strategic pivot to `presenton`.