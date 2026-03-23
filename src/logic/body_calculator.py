import logging
from typing import Dict, Any

# Setup module logger
logger = logging.getLogger(__name__)

# --- Modular Formula Definitions ---
# These internal functions map to Excel spreadsheet formulas.
# Isolating them allows engineering updates without breaking the logic flow.

def _calc_body_tension(size: float, yield_strength: float) -> float:
    """
    Placeholder formula for Body Tension.
    Returns a deterministic dummy value purely for the MVP logic engine test.
    
    Future API 5CT Implementation:
        Area = (pi/4) * (OD^2 - ID^2)
        Tension = Area * Yield Strength
    """
    # MVP Placeholder: 100,000 lbs * size multiplier
    return float(size * 100000.0)

def _calc_body_burst(size: float, yield_strength: float) -> float:
    """
    Placeholder formula for Body Burst.
    
    Future API 5CT Implementation (Barlow's formula):
        Burst = 0.875 * (2 * Yield * wall_thickness / OD)
    """
    # MVP Placeholder: 5,000 psi * size multiplier
    return float(size * 5000.0)

def _calc_body_collapse(size: float, yield_strength: float) -> float:
    """
    Placeholder formula for Body Collapse.
    
    Future API 5CT Implementation:
        Depends on calculated D/t ratio determining Elastic/Plastic/Transistion collapse.
    """
    # MVP Placeholder: 4,000 psi * size multiplier
    return float(size * 4000.0)


# --- Core Execution Logic ---

def calculate_body_values(inputs: Dict[str, Any]) -> Dict[str, float]:
    """
    Computes the mechanical body strength of the pipe (Tension, Burst, Collapse)
    based on the raw extraction inputs.

    Args:
        inputs (Dict[str, Any]): Dictionary containing at minimum 'size' and 'material'.
                                 e.g., {'size': '3.50', 'material': 'L80', ...}

    Returns:
        Dict[str, float]: Standardized schema matching the Normalization Layer:
            {'tension': float, 'burst': float, 'collapse': float}

    Raises:
        ValueError: If 'size' or 'material' are missing, null, or invalid formats.
    """
    # 1. Input Validation - Hard block missing identifiers
    raw_size = inputs.get("size")
    raw_material = inputs.get("material")

    if not raw_size or not raw_material:
        raise ValueError(f"Body calculation Validation Error: Missing 'size' or 'material' in inputs. Received: {inputs}")

    try:
        # Cast to float for predictable mathematical operations
        size_val = float(raw_size)
    except ValueError:
        raise ValueError(f"Body calculation Validation Error: 'size' ('{raw_size}') must be numeric.")

    # 2. Derive Material Yield Strength (Placeholder extraction logic for MVP)
    # E.g. "L80" -> 80,000 psi. If format is totally unexpected, fallback to 80ksi.
    try:
        material_grade = ''.join(c for c in raw_material if c.isdigit())
        yield_strength = float(material_grade) * 1000.0 if material_grade else 80000.0
    except Exception:
        logger.warning(f"Could not parse pure numerical yield strength from material '{raw_material}'. Defaulting to 80,000.")
        yield_strength = 80000.0

    logger.debug(f"Calculating Body Values for size={size_val}, yield_strength={yield_strength}")

    # 3. Call modular formulas
    tension = _calc_body_tension(size_val, yield_strength)
    burst = _calc_body_burst(size_val, yield_strength)
    collapse = _calc_body_collapse(size_val, yield_strength)

    # 4. Return canonical schema structure
    return {
        "tension": tension,
        "burst": burst,
        "collapse": collapse
    }


if __name__ == "__main__":
    # --- Simple MVP Test execution ---
    logging.basicConfig(level=logging.DEBUG)
    print("--- Running Body Calculator Tests ---")
    
    mock_inputs = {
        "top_connection": "VAM TOP BOX",
        "bottom_connection": "VAM TOP PIN",
        "size": "3.50",
        "material": "L80"
    }

    try:
        print(f"\nProcessing Valid Inputs: {mock_inputs}")
        results = calculate_body_values(mock_inputs)
        print("\n✅ Body Calculation Successful:")
        print(results)
    except Exception as e:
        print(f"\n❌ Expected Success, but Failed: {e}")

    try:
        print("\nProcessing Invalid Inputs (Missing size)...")
        calculate_body_values({"material": "L80"})
    except ValueError as e:
        print(f"✅ Successfully caught validation error: {e}")
