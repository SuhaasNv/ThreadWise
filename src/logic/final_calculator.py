import logging
from typing import Dict, Any

# Setup module logger for logic traceability
logger = logging.getLogger(__name__)

def compute_final(top: Dict[str, Any], bottom: Dict[str, Any], body: Dict[str, Any]) -> Dict[str, float]:
    """
    Computes the final governing performance ratings based on the engineering rule:
    Final Rating = MIN(Top Connection, Bottom Connection, Body Strength)
    
    Args:
        top (Dict[str, Any]): Normalized performance data for the top connection.
        bottom (Dict[str, Any]): Normalized performance data for the bottom connection.
        body (Dict[str, Any]): Calculated performance data for the pipe body.
        
    Returns:
        Dict[str, float]: The final limiting values for tension, burst, and collapse.
        
    Raises:
        ValueError: If any required key is missing or None across any of the inputs.
    """
    keys_to_evaluate = ["tension", "burst", "collapse"]
    final_output: Dict[str, float] = {}

    for key in keys_to_evaluate:
        # 1. Extraction: Pull the specific metric from all three components
        top_val = top.get(key)
        bottom_val = bottom.get(key)
        body_val = body.get(key)
        
        # 2. Validation: 'Hard Stop' on missing or None data.
        # Definitively prohibits ambiguous calculations (e.g., treating None as 0 or simply skipping).
        if top_val is None or bottom_val is None or body_val is None:
            logger.error(f"Data constraint violation for {key}: Top={top_val}, Bottom={bottom_val}, Body={body_val}")
            raise ValueError(
                f"Missing or None value encountered for '{key}'. "
                f"Top: {top_val}, Bottom: {bottom_val}, Body: {body_val}"
            )
            
        # 3. Type normalization: Ensure deterministic behavior by casting heavily to float
        try:
            values = [float(top_val), float(bottom_val), float(body_val)]
        except ValueError:
            raise ValueError(
                f"Non-numeric data found for '{key}'. "
                f"Top: {top_val}, Bottom: {bottom_val}, Body: {body_val}"
            )

        # 4. Core Logic Execution: The weakest link governs the completion string rating.
        final_output[key] = min(values)
        
        # Traceability: Log the breakdown so engineers can audit the exact logic used
        logger.debug(f"Governing {key.upper()}: min{values} -> {final_output[key]}")

    return final_output


if __name__ == "__main__":
    # --- Simple MVP Test execution ---
    logging.basicConfig(level=logging.DEBUG)
    print("--- Running Final Calculator Tests ---")
    
    mock_top = {"tension": 345000.0, "burst": 12000.0, "collapse": 11500.0}
    # Bottom connection has the weakest tension & collapse
    mock_bottom = {"tension": 330000.0, "burst": 12500.0, "collapse": 11000.0}
    # Body is strong but never the weakest link here
    mock_body = {"tension": 400000.0, "burst": 15000.0, "collapse": 14000.0}
    
    print("\n✅ Processing Valid Inputs:")
    try:
        final_ratings = compute_final(mock_top, mock_bottom, mock_body)
        print("Final Governing Values:")
        print(final_ratings)
    except Exception as e:
        print(f"Failed: {e}")
        
    print("\n❌ Processing Invalid Inputs (None handling):")
    # Setting burst to None forces a critical safety failure
    mock_bottom_missing = {"tension": 330000.0, "burst": None, "collapse": 11000.0}
    try:
        compute_final(mock_top, mock_bottom_missing, mock_body)
    except ValueError as e:
        print(f"Caught Expected Failure: {e}")
