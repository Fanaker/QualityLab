# QualityLab — release checklist

**Version:** 1.0.0  
**Date:** 2026-11-11  
**Scope:** Local-first QA demonstration, not a production QA platform.

## Verified in the creation environment
- FastAPI application imported and routes exercised with TestClient.
- Five API/domain checks passed (`tests/test_api.py`).
- One Playwright Chromium navigation check passed (`tests/test_browser.py`).
- `node --check web/app.js` passed.
- Five screenshot pages were rendered from the bundled UI using the API demo response: overview, cases, bugs, runs and coverage.

## What is simulated
- Historical sprint metrics, percentages, bugs and assignments preloaded for the demonstration.
- The real SUT has a small checkout quote implementation and six executable smoke checks.
- No hosting, company data, real payment gateway or external service.

## What to do on your machine
1. Install the Python dependencies.
2. Launch `uvicorn app.main:app --reload`.
3. Install Playwright Chromium to run the UI test if needed.
4. Check the README screenshots and optional Postman collection.
