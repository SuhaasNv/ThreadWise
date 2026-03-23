import logging
import time
from typing import Dict
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Setup basic module logger for traceability
logger = logging.getLogger(__name__)

# Constants for resilience
MAX_RETRIES = 3
RETRY_DELAY_SEC = 2
DEFAULT_ACTION_TIMEOUT_MS = 10000  # 10s timeout prevents hanging

# Placeholder vendor URL
VAM_URL = "https://example.com/vam-portal"

def _clean_value(val_str: str) -> float:
    """
    Helper to safely convert scraped strings (e.g., '120,500 psi') into pure floats.
    Ensures deterministic data types for downstream logic.
    """
    clean_str = ''.join(c for c in val_str if c.isdigit() or c == '.')
    try:
        return float(clean_str)
    except ValueError:
        raise ValueError(f"Failed to parse numerical value from scraped text: '{val_str}'")


def fetch_vam_data(connection: str, size: str) -> Dict[str, float]:
    """
    Fetches engineering performance data for a specific VAM connection and size.
    Uses Playwright to interact with the vendor's web application.

    Args:
        connection (str): The connection type (e.g., "VAM TOP").
        size (str): The size of the connection (e.g., "3.50").

    Returns:
        Dict[str, float]: Standardized dictionary containing:
            - tension (float)
            - burst (float)
            - collapse (float)

    Raises:
        RuntimeError: If all retry attempts to fetch data fail (Hard Stop).
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"[Attempt {attempt}/{MAX_RETRIES}] Fetching VAM data for {connection} - {size}")
            
            with sync_playwright() as p:
                # Launch browser. headless=True for production speed.
                # headless=False is useful for local debugging to see the SPA load.
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()

                # Set a strict timeout to avoid infinite hangs on broken vendor sites
                page.set_default_timeout(DEFAULT_ACTION_TIMEOUT_MS)

                # Step 1: Navigate to the vendor entry page
                page.goto(VAM_URL)
                
                # ------------------------------------------------------------------
                # MVP NOTE: The selectors below are explicitly robust placeholders.
                # Replace these with the actual ID, data-testid, or semantic HTML 
                # identifiers used on the real VAM website to prevent brittle scraping.
                # ------------------------------------------------------------------
                connection_selector = "select#connection_dropdown"
                size_selector = "select#size_dropdown"
                submit_btn_selector = "button#submit_btn"
                
                # Step 2: Handle dropdown interactions
                # Wait for the first element to ensure the SPA is hydrated and ready
                page.wait_for_selector(connection_selector, state="visible")
                page.select_option(connection_selector, label=connection)
                
                # Often, size dropdowns are populated dynamically after connection selection.
                # We wait for it to be visible/enabled before interacting.
                page.wait_for_selector(size_selector, state="visible")
                page.select_option(size_selector, label=size)

                # Step 3: Submit and wait for results
                page.click(submit_btn_selector)
                
                # Wait for the results container to render in the DOM
                results_table = "table#results_table"
                page.wait_for_selector(results_table, state="visible")

                # Step 4: Extract data 
                # .inner_text() fetches the exact textual value a user sees.
                tension_raw = page.locator("td[data-field='tensile_strength']").inner_text()
                burst_raw = page.locator("td[data-field='internal_yield']").inner_text()
                collapse_raw = page.locator("td[data-field='collapse_resistance']").inner_text()

                browser.close()

                # Step 5: Normalize and return the schema
                return {
                    "tension": _clean_value(tension_raw),
                    "burst": _clean_value(burst_raw),
                    "collapse": _clean_value(collapse_raw)
                }

        except PlaywrightTimeoutError as e:
            logger.warning(f"Timeout occurred during VAM scrap step (Network or DOM issue): {str(e)}")
        except Exception as e:
            logger.warning(f"Unexpected error during scraping attempt: {str(e)}")

        # Delay before retrying to let temporary vendor server issues resolve
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SEC)
            
    # Failed definitively. Do not fail silently.
    raise RuntimeError(f"Failed to fetch VAM data for {connection}-{size} after {MAX_RETRIES} attempts.")

if __name__ == "__main__":
    # --- Simple MVP Test execution ---
    logging.basicConfig(level=logging.INFO)
    print("--- Running VAM Fetcher Test (Expected to fail gracefully w/ dummy URL) ---")
    try:
        # Expected to hit the TimeoutError during retry loop 
        # because the 'example.com' DOM lacks the expected selectors.
        data = fetch_vam_data("VAM TOP", "3.50")
        print("\n✅ Successfully Extracted Data:")
        print(data)
    except Exception as e:
        print(f"\n❌ Fetch Exception Caught Successfully: {e}")
