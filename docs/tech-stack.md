# Tech Stack Definition: ThreadWise

**Status:** Recommended Architecture  
**Focus:** Cost-Efficiency, 5-10 Year Maintainability, Reliability  
**Domain:** Industrial Engineering / Oil & Gas  

---

## 1. Design Principles

- **Simplicity over Complexity:** Avoid distributed systems (microservices/Kubernetes); prioritize a single-process executable.
- **Cost-Efficiency:** Zero or near-zero fixed monthly costs for low-scale usage.
- **Maintainability:** Modular code where only the "adapters" (e.g., vendor scrapers) need updating when external sites change.
- **Reliability over Novelty:** Use mature, stable libraries (Python, Playwright) rather than experimental "AI-first" frameworks.
- **Auditability:** Every calculation must have a traceable path back to the source data.

---

## 2. Core Tech Stack Overview

| Layer | Technology | Purpose | Why Chosen |
| :--- | :--- | :--- | :--- |
| **Language** | **Python 3.10+** | Core Backend Logic | Best-in-class libraries for Excel, automation, and data handling. |
| **Web Automation** | **Playwright** | Vendor Data Extraction | Faster, more reliable than Selenium; built-in auto-waiting and modern SPA support. |
| **Excel Handler** | **openpyxl** | Template R/W | Native `.xlsx` support; preserves complex formatting and internal formulas. |
| **Validation** | **Pydantic** | Schema Enforcement | Ensures data integrity; flags "NULL" or "Empty" values before they hit the logic engine. |
| **Interface** | **Typer / Argparse** | CLI | Lightweight; easy for engineers to run via scripts or batch operations. |
| **Logging** | **Python Logging** | Traceability | Built-in, zero-dependency, and highly configurable (JSON/File). |
| **Storage** | **Filesystem / SQLite** | Data Persistence | Minimizes infrastructure costs; SQLite provides ACID compliance without a separate server. |

---

## 3. Backend (Python)

**Recommendation:** Python 3.10+ (Vanilla).
- **Why Python?** It is the standard for engineering and automation. Its ecosystem for Excel (openpyxl) and scraping (Playwright) is unrivaled, and it allows for rapid logic changes without recompilation.
- **No Heavy Frameworks:** For a low-scale system, Django or heavy async frameworks add unnecessary abstraction. Simple, synchronous Python modules are easier to maintain over a 10-year period.

---

## 4. Web Automation / Scraping (Playwright)

**Recommendation:** Playwright (Python).
- **Playwright vs. Selenium:** Playwright handles modern Single Page Applications (SPAs) much better with its "auto-wait" logic, reducing flaky scripts. It is also significantly faster and includes a GUI "Codegen" tool for rapid scraper development.
- **Scraping Strategy:** Fetch LIVE data only when needed. Use local headless browsers to avoid recurring costs of scraping services.
- **Optional Fallback:** If vendor sites implement extreme anti-bot measures (e.g., Cloudflare), a service like **Bright Data** can be integrated as a lightweight proxy layer.

---

## 5. Excel Processing (openpyxl & pandas)

**Recommendation:** `openpyxl` as the primary engine.
- **Why openpyxl?** It treats the Excel file as a document, preserving the user's colors, cell borders, and existing formulas.
- **Why NOT pandas (by default)?** Pandas is powerful for "Data Analysis" (dataframes) but it often creates "clean" copies of Excel files that strip away formatting. Only use pandas if we need to perform complex group-by operations on hundreds of rows.

---

## 6. Data Handling / Schema Layer (Pydantic)

**Recommendation:** Pydantic Models.
- **Why Pydantic?** In engineering, an incorrect number is a safety risk. Pydantic ensures that a "Tensile" value isn't just a string like `"12,000 LB"` but a validated float `12000.0`. It acts as a strict contract between the Scraper and the Logic Engine.

---

## 7. Logging & Monitoring

**Recommendation:** Python `logging` module + JSON formatting.
- **Traceability:** In an audit, we need to know: *"On 2026-03-23, what did the VAM website show for 3.50 inch L80?"*. Structured JSON logs allow us to store this metadata (URLs, timestamps, raw fields) permanently.

---

## 8. Storage

**Recommendation:** Local Filesystem + SQLite (optional).
- **Minimalist Approach:** Since usage is low, storing logs and outputs in a structured folder tree (`/logs`, `/outputs`) is often sufficient.
- **Why SQLite?** If we need a persistent cache (e.g., caching VAM lookups for 24h), SQLite is a zero-configuration database that lives in a single file on disk. No server, no cost, infinite reliability.

---

## 9. API Layer (Minimalist FastAPI)

- **Only Introduce If:** We need to integrate with other corporate tools or if multiple engineers need to hit a shared service.
- **Recommendation:** FastAPI. It is lightweight, typed, and auto-generates Swagger documentation.

---

## 10. CLI / Interface

**Recommendation:** Typer or standard `argparse`.
- **Reason:** Engineers are comfortable with CLI tools. It allows for batching (e.g., `python main.py --directory ./input_templates`) and is easier to maintain than a web UI.

---

## 11. Deployment Strategy

- **Primary:** Local execution on the engineer's machine.
- **Optional:** A simple **Azure VM** or **On-Premise Server** if we want a shared "Automated Inbox" (e.g., drop a file, system processes it).
- **Avoid:** Kubernetes or Serverless (AWS Lambda/Azure Functions). Managing Playwright browsers in serverless environments is complex and often more expensive than a simple, persistent VM.

---

## 12. AI Integration (Edge Cases Only)

- **Use Case 1:** Parsing unstructured PDF technical data sheets.
- **Use Case 2:** Visual validation (taking a screenshot of the scraper results and asking an LLM to "double-check" if the numbers match the GUI).
- **Constraint:** AI should be a "Reviewer," not the "Primary Logic."

---

## 13. Alternatives Considered

1.  **Node.js (Puppeteer):** Excellent for scraping, but the Python ecosystem for mathematical calculations and Excel handling is significantly stronger for this domain.
2.  **Excel Macros (VBA):** Very easy to build but impossible to maintain at scale, difficult to version control via Git, and poor at handling modern web scraping.
3.  **NoSQL (MongoDB):** Overkill for this schema. Our data is highly structured; relational models (SQLite) are safer for engineering data.

---

## 14. Cost Considerations

| Item | Estimated Cost | Optimization |
| :--- | :--- | :--- |
| **Development** | $0 (Open Source) | Python/Playwright libraries are free. |
| **Infrastructure** | $0 (Local) | Runs on engineer's existing hardware. |
| **Scraping** | $0 - $20/mo | Only pay if premium proxies are needed for anti-bot. |
| **Logic/AI** | $0 - $5/mo | Local logic is free; optional Gemini/GPT-4 API for validation is pay-as-you-go. |

---

## 15. Future Stack Evolution

- **Step 1:** Add a **Caching Layer** (SQLite) to avoid hitting vendor sites for the same request within 24h.
- **Step 2:** Build a **Streamlit Dashboard** as a GUI-on-top of the CLI.
- **Step 3:** Move to **FastAPI + Docker** if the system needs to be deployed as a corporate web-service.
