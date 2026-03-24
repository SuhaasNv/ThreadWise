# ThreadWise

Automated engineering workflow for completion products in the Oil & Gas industry.

## Project status

This repo is an **experiment** and a **minimal MVP**—a learning and portfolio sketch, not a finished or supported product. It is **not** production-ready engineering software: no warranty of correctness, completeness, or ongoing maintenance. Treat outputs as illustrative only unless you validate them yourself under your own processes.

## 🚀 Overview
ThreadWise automates the manual process of extracting vendor connection data (VAM, Hydril), performing body calculations, and auto-filling engineering release templates in Excel.

## 📂 Project Structure

```text
threadwise/
├── src/                # Core implementation
│   ├── extraction/     # Extracts specs from Excel
│   ├── vendor/         # Vendor-specific Playwright scripts
│   ├── normalization/  # Mappings and Pydantic schemas 
│   ├── logic/          # Engineering formulas & MIN logic
│   ├── excel/          # Excel reading/writing logic
│   ├── logging/        # Traceability and audit logs
│   └── main.py         # Entry point (CLI)
├── tests/              # Unit & Integration tests
├── data/               # Excel templates & outputs (ignored in git)
├── scripts/            # Helper bash/python scripts
├── docs/               # PRD, Implementation Plan, Research
├── .env                # Secrets (e.g., vendor credentials if applicable)
├── .gitignore          # Git ignores (avoids committing data/logs)
├── requirements.txt    # Python dependencies
└── README.md
```

## 🛠 Tech Stack
- **Language:** Python 3.10+
- **Web Automation:** Playwright
- **Excel Handling:** openpyxl / pandas
- **Validation:** Pydantic

## 🏁 Getting Started

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```
4. Run the orchestrator:
   ```bash
   python src/main.py --input data/template.xlsx
   ```

## 📄 Documentation
For detailed project documentation, see the following:
- [Product Requirements Document (PRD)](docs/threadwise_prd.md)
- [Implementation Plan](docs/implementation-plan.md)
- [Tech Stack Definition](docs/tech-stack.md)
