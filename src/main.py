import sys
import argparse

# ThreadWise Modules
from extraction.excel_extractor import extract_inputs
from vendor.vam_fetcher import fetch_vam_data
from normalization.adapter import VAMAdapter
from logic.body_calculator import calculate_body_values
from logic.final_calculator import compute_final
from excel.writer import write_results
from app_logging.logger import log_info, log_error


def run_pipeline(file_path: str) -> None:
    """
    Executes the end-to-end ThreadWise automation pipeline.
    Ensures safe, strict sequential processing based on the User Flow documentation.
    """
    try:
        log_info("Starting ThreadWise Pipeline", {"input_file": file_path})
        
        # STEP 1: Extraction
        log_info("Step 1/6: Extracting inputs from Excel...")
        inputs = extract_inputs(file_path)
        log_info("Extraction successful", inputs)
        
        # Standard input schema variables
        top_conn = inputs["top_connection"]
        bottom_conn = inputs["bottom_connection"]
        size = inputs["size"]
        
        # STEP 2: Vendor Fetching
        log_info("Step 2/6: Fetching Live Vendor Data (Top & Bottom)...")
        # NOTE: For MVP, we pass both to the VAM fetcher. 
        # In Phase 2, an Orchestrator/Factory pattern will direct this to Hydril if needed.
        raw_top_data = fetch_vam_data(top_conn, size)
        raw_bottom_data = fetch_vam_data(bottom_conn, size)
        log_info("Vendor fetch successful")
        
        # STEP 3: Normalization
        log_info("Step 3/6: Normalizing vendor specific schemas...")
        adapter = VAMAdapter()
        norm_top = adapter.normalize(raw_top_data)
        norm_bottom = adapter.normalize(raw_bottom_data)
        log_info("Normalization rigorous check successful", {"top": norm_top, "bottom": norm_bottom})
        
        # STEP 4: Body Calculation
        log_info("Step 4/6: Calculating internal Pipe Body Strength...")
        body_data = calculate_body_values(inputs)
        log_info("Body calculation successful", body_data)
        
        # STEP 5: Governing Logic Application
        log_info("Step 5/6: Applying String Logic [Rule: MIN(Top, Bottom, Body)]...")
        final_ratings = compute_final(norm_top, norm_bottom, body_data)
        log_info("Final Logic applied definitively", final_ratings)
        
        # STEP 6: Output / Save
        log_info("Step 6/6: Writing final output backwards-safely to Excel template...")
        write_results(file_path, final_ratings)
        
        # --- UI SUMMARY --- #
        print("\n" + "="*60)
        print("🎯 THREADWISE EXECUTION SUCCESSFUL 🎯")
        print("="*60)
        print(f"File Updated   : {file_path}")
        print(f"String Assembly: {top_conn} -> {bottom_conn} ({size}\")")
        print("-" * 60)
        print(f"Final Tension  : {final_ratings['tension']:,.2f} lbs")
        print(f"Final Burst    : {final_ratings['burst']:,.2f} psi")
        print(f"Final Collapse : {final_ratings['collapse']:,.2f} psi")
        print("="*60 + "\n")
        
        log_info("Pipeline Completed Successfully.")

    except Exception as e:
        log_error("Pipeline HALTED due to a critical workflow error", error=e)
        print("\n❌ THREADWISE PIPELINE FAILED: Please check the structured JSON logs in `/logs` for a full traceback and metric payload.")
        sys.exit(1)


def main():
    """
    Entry point for the CLI tool.
    Accepts the engineering template via `--file` argument.
    """
    parser = argparse.ArgumentParser(description="ThreadWise: Automated Engineering Workflow Pipeline")
    parser.add_argument(
        "--file", 
        type=str, 
        help="Absolute or relative path to the input/output Excel template",
        required=True
    )
    
    # Parse the arguments and trigger the unified flow
    args = parser.parse_args()
    
    # In order to make relative imports inside src work, we insert src to sys_path.
    # We do a tiny bit of path hacking just in case someone runs it purely from the root folder.
    import os
    src_path = os.path.abspath(os.path.dirname(__file__))
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    run_pipeline(args.file)

if __name__ == "__main__":
    main()
