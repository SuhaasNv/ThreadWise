# Implementation Plan: ThreadWise

**Status:** Technical Blueprint  
**Target:** Senior Software Engineer / Solo Architect  
**Tech Stack:** Python, Playwright, openpyxl, Pydantic  

---

## 1. Project Setup

### 1.1 Folder Structure
A flat, modular structure designed for low-scale, high-reliability execution.

```text
threadwise/
├── data/               # Excel templates & temporary input files
├── docs/               # PRD, Implementation Plan, Research
├── logs/               # Traceability logs (JSON, MD, TXT)
├── src/                # Core implementation
│   ├── main.py         # Entry point (CLI)
│   ├── orchestrator.py  # Workflow management
│   ├── excel/          # Excel reading/writing logic
│   ├── scrapers/       # Vendor-specific Playwright scripts
│   ├── logic/          # Engineering formulas & MIN logic
│   ├── models/         # Pydantic schemas (Normalization)
│   └── utils/          # Logging, custom errors
├── tests/              # Unit & Integration tests
├── .env                # Secrets (if any, e.g., vendor creds)
├── requirements.txt
└── README.md
```

### 1.2 Environment & Dependencies
- **Python Version:** 3.10+
- **Virtual Env:** `python -m venv venv`
- **Dependencies:**
  - `playwright`: Web automation for vendor data extraction.
  - `openpyxl`: Heavy-duty Excel R/W (preserving formatting).
  - `pandas`: (Optional) For complex tabular data manipulation.
  - `pydantic`: For strict data validation and schema normalization.
  - `pytest`: For unit and integration testing.

---

## 2. System Architecture Overview

ThreadWise follows a **Modular Pipeline Architecture**. Each stage passes a validated object to the next, ensuring failures are isolated.

**Data Flow:**
1.  **Input:** `Excel Manager` extracts specs → returns `SpecModel`.
2.  **Orchestration:** `Orchestrator` triggers `ScraperManager`.
3.  **Extraction:** `Playwright Scraper` fetched raw data → returns `VendorData`.
4.  **Normalization:** `Normalizer` maps `VendorData` → `StandardPerformanceModel`.
5.  **Logic:** `LogicEngine` computes Body Strength & applies `MIN()` rule.
6.  **Output:** `Excel Manager` writes back to the template.

---

## 3. Development Phases

### Phase 1 — MVP (Week 1)
- **Goal:** One template, one vendor (VAM), one successful output.
- **Tasks:** Core `orchestrator.py`, basic `vam_scraper.py`, and `excel_manager.py`.

### Phase 2 — Multi-Vendor Support
- **Goal:** Add Hydril and handle schema differences.
- **Tasks:** Abstract scrapers into an **Adapter Pattern**, implement the `StandardPerformanceModel`.

### Phase 3 — Robustness
- **Goal:** Engineering-grade reliability.
- **Tasks:** Comprehensive logging, "Hard Stop" error handling, and Pydantic validation of all vendor values.

### Phase 4 — Enhancements
- **Goal:** Speed and usability.
- **Tasks:** Caching (SQLite or JSON), CLI progress bars (`rich` or `tqdm`), and optional Streamlit UI.

---

## 4. Module-by-Module Implementation

### 4.1 Input Extraction Module (`src/excel/reader.py`)
- **Action:** Open `.xlsx`, read specific cell ranges (e.g., `B5:B10`).
- **Schema:** Use Pydantic `DesignSpecs` to ensure Size/Weight are floats, not strings.
- **Edge Case:** Handle empty cells or incorrect material formats with a clear `ExtractionError`.

### 4.2 Vendor Fetch Module (`src/scrapers/base.py`, `vam.py`)
- **Playwright Setup:** Launch in `headless=False` for debug/validation, `headless=True` for production.
- **Strategy:**
  - `navigate()` to vendor site.
  - `select_option()` for Size, Material, Weight.
  - `inner_text()` to extract Tensile, Burst, Collapse.
- **Retry Logic:** Exponential backoff (3 attempts) using a decorator.

### 4.3 Normalization Layer (`src/models/performance.py`)
- **Adapter Pattern:** Define a `BaseScraper` interface. Each vendor class implements `fetch()`.
- **Normalization:** Map VAM's "Yield" and Hydril's "Tension" both to `tensile_lb`.

### 4.4 Body Calculation Engine (`src/logic/body_calcs.py`)
- **Strategy:** Convert internal Excel formulas (e.g., `Burst = 0.875 * (2 * Yield * t / D)`) into Python functions.
- **Function Structure:**
  ```python
  def calculate_body_burst(yield_strength: float, wall_thickness: float, diameter: float) -> float:
      # Apply API 5CT or internal proprietary formula
      return 0.875 * (2 * yield_strength * wall_thickness / diameter)
  ```

### 4.5 Business Logic Engine (`src/logic/governing_rule.py`)
- **Action:** Take `TopConn`, `BottomConn`, and `Body` performance objects.
- **Logic:** `FinalTensile = min(top.tensile, bottom.tensile, body.tensile)`.
- **Validation:** If any source value is missing, flag as "Critical Failure" rather than outputting a 0.

### 4.6 Excel Writer Module (`src/excel/writer.py`)
- **Action:** Locate target cells for `Final Tensile`, `Final Burst`, etc.
- **Formatting:** Use `openpyxl` to write values WITHOUT stripping existing styles/borders/formulas in the template.

### 4.7 Logging System (`src/utils/logger.py`)
- **Structure:** `logs/{timestamp}_{project_name}.log`
- **Content:** Log the input specs, the exact URLs visited, the raw values found, and the final logic breakdown.

---

## 5. Data Flow Walkthrough

1.  **Start:** `main.py --input data/spec.xlsx`
2.  **Read:** `ExcelReader` grabs `3.50", 9.20ppf, L80, VAM TOP`.
3.  **Fetch:** `VamScraper` navigates, selects params, pulls `Tensile: 345,000`.
4.  **Calc:** `BodyEngine` calculates `Body Tensile: 400,000`.
5.  **Logic:** `LogicEngine` runs `min(345k, 345k, 400k)` → Result: `345k`.
6.  **Write:** `ExcelWriter` saves `345,000` into `Cell D40`.
7.  **Log:** Traceability file saved for QA review.

---

## 6. Error Handling Strategy

- **Vendor Site Failure:** Catch `PlaywrightTimeoutError`. Trigger retry. If final fail, log source URL and stop.
- **Missing Fields:** If a scraper can't find "Collapse," raise `DataIntegrityError`.
- **Invalid Data:** `Pydantic` will catch if "12,000 PSI" is scraped as a string instead of being converted to an int.
- **Strategy:** **Fail Fast**. In engineering, an incorrect value is worse than no value.

---

## 7. Testing Plan

- **Unit Tests:** Test calculation functions with known Excel results.
- **Mock Scrapers:** Use `unittest.mock` to simulate vendor website responses for CI/CD speed.
- **E2E Test:** Run a full cycle with a "Golden Template" and verify the output file hashes match expected results.

---

## 8. Performance Considerations

- **Caching:** Cache vendor responses by `(Vendor, Connection, Size, Weight, Material)` for 24 hours.
- **Parallel Scaping:** Use `asyncio` with Playwright to fetch Top and Bottom connection data simultaneously.
- **Resource Usage:** Close browser contexts immediately after extraction to keep the memory footprint low.

---

## 9. Deployment Strategy

- **Phase 1:** Single user runs script locally.
- **Phase 2:** Package as a standalone executable using `PyInstaller` so engineers don't need Python installed.
- **Phase 3:** Create a simple CLI interface for batch processing multiple templates in a folder.

---

## 10. Future Improvements

- **AI Validation Layer:** Use an LLM to compare screenshot of vendor site vs. extracted text to verify OCR/scraping accuracy.
- **Web Dashboard:** A simple FastAPI + Streamlit interface to manage templates and view historical logs.
- **Scheduling:** Automatic "Audit Run" every week to check if vendor values in the common specs have changed.
