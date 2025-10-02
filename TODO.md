# Project TODO List

This document tracks the development tasks for the Interactive Poster Generator project.

## Phase 1 & 2: Architecture, Quality, and DX (Completed)

-   **[X]** All Phase 1 and 2 tasks related to refactoring, testing, and code quality have been successfully completed and committed.

## Phase 3: Architectural Transformation: Integrating 'presenton' (In Progress)

**Strategic Direction:** The project will pivot to use `presenton` as the core presentation generation engine. Our backend will be transformed into a **Backend for Frontend (BFF)**.

**Implementation Plan:** We will perform a manual, "Docker-less" installation of `presenton` by incrementally installing and verifying each dependency.

-   **[ ] 1. Setup `presenton` Source Code:**
    -   [ ] Clone the `presenton` repository from GitHub.
-   **[ ] 2. Incremental System Dependency Installation:**
    -   [ ] Install `nginx`
    -   [ ] Install `curl`
    -   [ ] Install `libreoffice`
    -   [ ] Install `fontconfig`
    -   [ ] Install `chromium`
    -   [ ] Install `nodejs` (Version 20)
    -   [ ] Install `ollama`
-   **[ ] 3. Incremental Language Dependency Installation:**
    -   [ ] Install all Python packages from `Dockerfile.dev` via `pip`.
    -   [ ] Install all Node.js packages by running `npm install` in the `servers/nextjs` directory.
-   **[ ] 4. Staged Service Activation & BFF Refactoring:**
    -   [ ] Configure and start `nginx`.
    -   [ ] Sequentially start `ollama`, `fastapi`, `mcp_server`, and `nextjs`.
    -   [ ] Once all `presenton` services are running locally, begin refactoring our backend to act as a BFF.

## Known Issues / Blockers

-   **[CRITICAL] Unstable Sandbox Environment:**
    -   **Symptom:** Fundamental system commands (`git clone`, `apt-get`, `docker`) have failed with inconsistent errors (`IsADirectoryError`, `no space left on device`, `PermissionDenied`).
    -   **Mitigation Strategy:** The current "Incremental Installation" plan for Phase 3 is designed to systematically work around or pinpoint the source of this instability. Each step will be small and verifiable.
-   **[LOW] Frontend Verification (`Playwright`) Blocked:**
    -   **Symptom:** Playwright tests fail with a `TimeoutError`.
    -   **Root Cause:** Believed to be a symptom of the larger environmental instability. De-prioritized until Phase 3 is addressed.