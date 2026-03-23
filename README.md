# ThreadWise

Automated engineering workflow for completion products in the Oil & Gas industry.

## 🚀 Overview
ThreadWise automates the manual process of extracting vendor connection data (VAM, Hydril), performing body calculations, and auto-filling engineering release templates in Excel.

## 🛠 Tech Stack
- **Language:** Python 3.10+
- **Web Automation:** Playwright
- **Excel Handling:** openpyxl / pandas
- **Validation:** Pydantic

## 📂 Project Structure
- `src/`: Core logic and scrapers.
- `docs/`: PRD and technical documentation.
- `data/`: Excel templates and temporary storage.
- `tests/`: Unit and integration tests.
- `logs/`: Traceability logs from execution runs.

## 🏁 Getting Started
1. Install dependencies: `pip install -r requirements.txt`
2. Install Playwright browsers: `playwright install chromium`
3. Run the orchestrator: `python src/orchestrator.py --input data/template.xlsx`

## 📄 Documentation
For detailed project documentation, see the following:
- [Product Requirements Document (PRD)](docs/threadwise_prd.md)
- [Implementation Plan](docs/implementation-plan.md)
- [Tech Stack Definition](docs/tech-stack.md)
