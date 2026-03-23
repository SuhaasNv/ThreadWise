import logging
import time
from typing import Dict
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Setup basic module logger for traceability
logger = logging.getLogger(__name__)

# Constants for resilience
MAX_RETRIES = 3
RETRY_DELAY_SEC = 2
DEFAULT_ACTION_TIMEOUT_MS = 20000  # Increased to 20s for Angular SPA loads
MOCK_MODE = False  # Turned OFF to hit the real VAM Configurator

# Actual Vendor Portal URL
VAM_URL = "https://www.vamservices.com/product/configurator"

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
    if MOCK_MODE:
        logger.info(f"MOCK_MODE ENABLED: Simulating fetch for {connection} - {size}")
        time.sleep(1.5)  # Simulate network latency
        return {
            "tension": 345000.0 if "BOX" in connection.upper() else 330000.0,
            "burst": 12000.0 if "BOX" in connection.upper() else 12500.0,
            "collapse": 11500.0 if "BOX" in connection.upper() else 11000.0
        }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"[Attempt {attempt}/{MAX_RETRIES}] Fetching VAM data for {connection} - {size}")
            
            with sync_playwright() as p:
                # Launch browser. headless=True for production speed.
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                page.set_default_timeout(DEFAULT_ACTION_TIMEOUT_MS)

                # Step 1: Navigate to the real VAM Angular Configurator
                page.goto(VAM_URL, wait_until="domcontentloaded")
                
                # Format specific vendor sizes (e.g. 3.50 to '3-1/2' or generic matching)
                formatted_size = str(size).replace(".5", "-1/2").replace(".50", "-1/2")
                if not "-" in formatted_size and not "." in formatted_size:
                    formatted_size += " in."
                
                # ------------------------------------------------------------------
                # Authentic Playwright Navigation Steps for VAMServices.com
                # ------------------------------------------------------------------
                
                # Format specific connection names to match Vendor standard
                # Excel typically appends ' BOX' or ' PIN', but VAM just wants the base connection
                clean_connection = connection.upper().replace(" BOX", "").replace(" PIN", "").strip()
                
                # Wait for the Connection search box to hydrate
                search_input = "input.connection-search-input"
                page.wait_for_selector(search_input, state="visible")
                page.fill(search_input, clean_connection)
                
                # Click the matching div in the populated dropdown
                page.click(f"//div[contains(text(), '{clean_connection}')]")
                
                # Navigate to the OD (Size) dropdown
                od_input = "input[placeholder='select OD']"
                page.wait_for_selector(od_input, state="visible")
                page.fill(od_input, formatted_size)
                
                # Click the first matching result in the OD dropdown
                page.click(f"//mat-option//span[contains(text(), '{formatted_size}')]")
                
                # Click the View CDS (Connection Data Sheet) button to load results
                page.click("//button[span[contains(text(), 'View CDS')]]")

                # Move into the formal Connection Data view header
                page.click("//a[contains(text(), 'Connection Data')]")

                # Step 4: Extract data from the Joint Performances cards
                # Wait safely for the specific Angular card values to populate
                page.wait_for_selector("xpath=//div[div[span[contains(text(), 'Tension Strength, with Sealability')]]]", state="visible")

                # Extract Tension (Tensile Strength) By Label
                tension_raw = page.locator("xpath=//div[div[span[contains(text(), 'Tension Strength, with Sealability')]]]//span[contains(@class, 'ng-star-inserted')]").inner_text()
                
                # Extract Burst (Internal Pressure Resistance) By Label
                burst_raw = page.locator("xpath=//div[div[span[contains(text(), 'Internal Pressure Resistance')]]]//span[contains(@class, 'ng-star-inserted')]").inner_text()
                
                # Extract Collapse (External Pressure Resistance) By Label
                collapse_raw = page.locator("xpath=//div[div[span[contains(text(), 'External Pressure Resistance')]]]//span[contains(@class, 'ng-star-inserted')]").inner_text()

                browser.close()

                # Cleanup strings (e.g., '160 klb' -> 160000.0)
                tension_val = _clean_value(tension_raw)
                if "klb" in tension_raw.lower():
                    tension_val *= 1000.0
                    
                return {
                    "tension": tension_val,
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
