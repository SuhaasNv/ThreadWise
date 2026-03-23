import os
import openpyxl
from typing import Dict, Optional

# Default configuration mapping fields to Excel cell coordinates
DEFAULT_CELL_MAPPING = {
    "top_connection": "B5",
    "bottom_connection": "B6",
    "size": "B7",
    "material": "B8"
}

def extract_inputs(
    file_path: str, 
    cell_mapping: Optional[Dict[str, str]] = None,
    sheet_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Extracts structured input fields from an Excel engineering template.

    Args:
        file_path (str): The absolute or relative path to the Excel (.xlsx) file.
        cell_mapping (Dict[str, str], optional): A dictionary mapping input keys to 
            Excel cell coordinates. Defaults to DEFAULT_CELL_MAPPING.
        sheet_name (str, optional): The specific sheet to read from. 
            Defaults to the active sheet if None.

    Returns:
        Dict[str, str]: A dictionary containing the extracted values:
            - top_connection
            - bottom_connection
            - size
            - material

    Raises:
        FileNotFoundError: If the provided file_path does not exist.
        ValueError: If any required values are missing or blank in the Excel file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found at path: {file_path}")

    # Use default mapping if none is provided via arguments
    mapping = cell_mapping or DEFAULT_CELL_MAPPING
    
    # Load workbook using data_only=True to read actual values instead of formulas
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb[sheet_name] if sheet_name else wb.active
    
    extracted_data: Dict[str, str] = {}
    missing_fields = []

    for key, cell_coord in mapping.items():
        cell_value = sheet[cell_coord].value
        
        # Validation: Check for None or purely empty whitespace values
        if cell_value is None or str(cell_value).strip() == "":
            missing_fields.append(f"{key} (Cell {cell_coord})")
        else:
            # We strictly cast to string and clean whitespace to normalize formatting
            extracted_data[key] = str(cell_value).strip()

    wb.close()

    # Hard Stop: Prevent ambiguous data from reaching the logic engine
    if missing_fields:
        raise ValueError(f"Extraction Error: Missing or blank required fields in Excel: {', '.join(missing_fields)}")

    return extracted_data

if __name__ == "__main__":
    # --- Simple Test Example ---
    # Setup: Create a dummy workbook to test the logic without external dependencies
    test_file_path = "test_dummy.xlsx"
    
    try:
        # Create a mock Excel file purely for testing
        test_wb = openpyxl.Workbook()
        test_ws = test_wb.active
        test_ws["B5"] = "VAM TOP BOX"
        test_ws["B6"] = "VAM TOP PIN"
        test_ws["B7"] = 3.50  # Float to test string conversion
        test_ws["B8"] = "L80"
        test_wb.save(test_file_path)
        
        print(f"--- Running Excel Extractor Test ---")
        print(f"Mock file created at: {test_file_path}")
        
        # Execute module
        extracted = extract_inputs(test_file_path)
        
        print("\n✅ Extraction Successful:")
        for k, v in extracted.items():
            print(f"  {k}: {v} (Type: {type(v).__name__})")
            
    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
    finally:
        # Clean up mock file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            print(f"\nCleaned up mock file: {test_file_path}")
