import logging
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

# Ensure the logs output directory exists in the environment
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

class JsonFormatter(logging.Formatter):
    """
    Custom formatter to output logs as structured JSON strings.
    This is crucial for machine-readability when debugging production 
    issues or auditing 10-year engineering release records.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "filename": record.filename,
            "line": record.lineno,
            "message": record.getMessage()
        }
        
        # If the logging call passed a dictionary in the 'extra' kwarg,
        # extract 'structured_data' and embed it securely into the JSON output.
        if hasattr(record, "structured_data"):
            log_obj["data"] = getattr(record, "structured_data")
            
        # Capture the exception traceback explicitly if an error occurred
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)


def setup_structured_logger(name: str = "ThreadWise") -> logging.Logger:
    """
    Initializes a production-grade logger that outputs raw JSON strictly to a file.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding multiple duplicate handlers if this is called repeatedly
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.DEBUG)
    
    # File Handler for permanent JSON Traceability
    log_file = os.path.join(LOGS_DIR, f"threadwise_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JsonFormatter())
    
    logger.addHandler(file_handler)
    
    return logger

# Create a singleton logger instance for our helper functions to utilize directly
_logger = setup_structured_logger()

# --- Helper Methods ---

def log_info(message: str, data: Optional[Dict[str, Any]] = None) -> None:
    """
    Helper function to log structured informational data.
    
    Args:
        message (str): Contextual message (e.g., "Extracted Inputs")
        data (dict, optional): The dictionary to store (e.g., input values, results)
    """
    # Output clearly to console for the operational CLI user
    console_msg = f"INFO: {message}"
    if data:
        console_msg += f" | {data}"
    print(console_msg)
    
    # Output structured JSON payload to the permanent engineering log file
    extra = {"structured_data": data} if data else {}
    _logger.info(message, extra=extra)


def log_error(message: str, error: Exception, data: Optional[Dict[str, Any]] = None) -> None:
    """
    Helper function to critically log errors with deep tracebacks and contextual payload.
    
    Args:
        message (str): Contextual error message (e.g., "Vendor Scrape Failed")
        error (Exception): The actual exception caught
        data (dict, optional): Any local variables or context (e.g., {"url": "...", "size": "3.5"})
    """
    # Output to console for user alerting
    print(f"❌ ERROR: {message} | Exception: {str(error)}")
    
    # Format extra keys securely
    extra = {"structured_data": data} if data else {}
    
    # Utilize exc_info=error to automatically inject the stack trace into the JSON file
    _logger.error(message, exc_info=error, extra=extra)


if __name__ == "__main__":
    # --- Simple MVP Test Execution ---
    print(f"--- Running Logger Test ---")
    log_info("Pipeline Started", {"mode": "test_run"})
    
    # 1. Test Logging Input Values
    mock_inputs = {
        "top_connection": "VAM TOP BOX",
        "size": "3.50",
        "material": "L80"
    }
    log_info("Extracted Raw Inputs", mock_inputs)
    
    # 2. Test Logging Computed Results
    mock_results = {"tension": 330000.0, "burst": 12000.0}
    log_info("Generated Engineering Calculation", mock_results)
    
    # 3. Test Error Logging
    try:
        raise ValueError("Timeout extracting from dropdown")
    except Exception as e:
        log_error("Vendor Fetch Failure (Hard Stop Encountered)", error=e, data={"vendor": "VAM", "size": "3.50"})
        
    print(f"\n✅ Audit logs written successfully to: {LOGS_DIR}")
    
    # Verification: Read the last line of the newly created log file
    log_files = sorted(os.listdir(LOGS_DIR))
    if log_files:
        latest_log = os.path.join(LOGS_DIR, log_files[-1])
        print("\n--- Snippet of JSON structured file output ---")
        try:
            with open(latest_log, 'r') as f:
                lines = f.readlines()
                # Print just the info record and error record as a raw json sample
                print(lines[1].strip()[:100] + "...")
                print(lines[-1].strip()[:100] + "...")
        except Exception:
            pass
