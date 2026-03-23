import os
import sys
import tempfile
import streamlit as st
import pandas as pd
import traceback

# --- Path Configuration ---
# Ensures the UI can import our backend modules cleanly 
# without relying on PYTHONPATH environment variables.
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from extraction.excel_extractor import extract_inputs
from vendor.vam_fetcher import fetch_vam_data
from normalization.adapter import VAMAdapter
from logic.body_calculator import calculate_body_values
from logic.final_calculator import compute_final
from excel.writer import write_results
from app_logging.logger import log_info, log_error

# --- UI Configuration ---
st.set_page_config(
    page_title="ThreadWise",
    page_icon="⚙️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom minimal styling to enforce engineering tools aesthetic
st.markdown("""
    <style>
    .stProgress .st-bo { background-color: #2e7d32; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem; }
    </style>
""", unsafe_allow_html=True)


def display_inputs(inputs: dict) -> None:
    """Helper to cleanly render the extracted Excel specifications"""
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Top Connection", inputs.get("top_connection", "N/A"))
    col2.metric("Bottom Connection", inputs.get("bottom_connection", "N/A"))
    col3.metric("Size (inch)", f"{inputs.get('size', 'N/A')}")
    col4.metric("Material", inputs.get("material", "N/A"))


def render_results_table(top: dict, bottom: dict, body: dict, final: dict):
    """Renders the numerical logic payload into a clean comparison table"""
    data = [
        {"Component": "Top Connection", "Tension (lbs)": top["tension"], "Burst (psi)": top["burst"], "Collapse (psi)": top["collapse"]},
        {"Component": "Bottom Connection", "Tension (lbs)": bottom["tension"], "Burst (psi)": bottom["burst"], "Collapse (psi)": bottom["collapse"]},
        {"Component": "Pipe Body", "Tension (lbs)": body["tension"], "Burst (psi)": body["burst"], "Collapse (psi)": body["collapse"]},
        {"Component": "✅ FINAL STRING (MIN)", "Tension (lbs)": final["tension"], "Burst (psi)": final["burst"], "Collapse (psi)": final["collapse"]}
    ]
    df = pd.DataFrame(data)
    
    # Format floats with commas for readability
    format_mapping = {"Tension (lbs)": "{:,.0f}", "Burst (psi)": "{:,.0f}", "Collapse (psi)": "{:,.0f}"}
    st.table(df.style.format(format_mapping))


def main():
    # --- Header ---
    st.title("⚙️ ThreadWise")
    st.subheader("Engineering Workflow Automation")
    st.markdown("Automated generation of Completion Product Release Documents.")
    st.markdown("---")

    # --- Section: File Upload ---
    st.header("1. Upload Engineering Template")
    uploaded_file = st.file_uploader(
        "Upload the specific `.xlsx` file containing the initial configuration constraints.", 
        type=["xlsx"], 
        help="The system will read this file, extract parameters, and overwrite target cells with the final calculated findings."
    )

    if uploaded_file is not None:
        st.success(f"File '{uploaded_file.name}' staged in memory.")
        
        # Save securely to a temporary path so the backend openpyxl can read it cleanly
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        try:
            # --- Section: Input Preview ---
            st.header("2. Extracted Input Parameters")
            with st.spinner("Parsing standard fields from Excel..."):
                inputs = extract_inputs(tmp_path)
            
            display_inputs(inputs)
            st.markdown("---")

            # --- Section: Action Trigger ---
            st.header("3. Execute Automation")
            st.info("The system will dynamically fetch live vendor data and apply the governing MIN() engineering rule.")
            
            if st.button("🚀 Run ThreadWise Pipeline", use_container_width=True, type="primary"):
                # Setup progress bar and status text
                progress_bar = st.progress(0, text="Initializing Pipeline...")
                status_box = st.empty()

                try:
                    log_info("Pipeline triggered via UI", {"file": uploaded_file.name})

                    # STEP 1: Process Vendor Fetch
                    status_box.info("Fetching Vendor Data (Top)...")
                    raw_top = fetch_vam_data(inputs["top_connection"], inputs["size"])
                    progress_bar.progress(25, text="Fetching Vendor Data (Bottom)...")
                    
                    raw_bottom = fetch_vam_data(inputs["bottom_connection"], inputs["size"])
                    progress_bar.progress(50, text="Normalizing Data...")

                    # STEP 2: Normalization
                    status_box.info("Normalizing schemas using adapters...")
                    adapter = VAMAdapter()
                    norm_top = adapter.normalize(raw_top)
                    norm_bottom = adapter.normalize(raw_bottom)
                    progress_bar.progress(70, text="Calculating Body Metrics...")

                    # STEP 3: Body Calculations & Logic
                    status_box.info("Applying Engineering Body Formulas...")
                    body_data = calculate_body_values(inputs)
                    progress_bar.progress(85, text="Calculating Final Governing Constraints...")

                    status_box.info("Applying Final MIN() Logic Rule...")
                    final_ratings = compute_final(norm_top, norm_bottom, body_data)
                    progress_bar.progress(95, text="Writing Output File...")

                    # STEP 4: Output Writing
                    status_box.info("Overwriting Excel metrics...")
                    write_results(tmp_path, final_ratings)
                    
                    progress_bar.progress(100, text="Execution Complete.")
                    status_box.success("🎉 Process successfully completed!")
                    st.toast("Pipeline execution successful!", icon="✅")

                    st.markdown("---")

                    # --- Section: Results ---
                    st.header("4. Execution Results")
                    render_results_table(norm_top, norm_bottom, body_data, final_ratings)
                    st.markdown("---")

                    # --- Section: Download Output ---
                    st.header("5. Download Release Document")
                    st.markdown("Review the raw output below and download the final overwritten template for distribution.")
                    
                    with open(tmp_path, "rb") as final_file:
                        st.download_button(
                            label="📥 Download Updated Excel Template",
                            data=final_file,
                            file_name=f"ThreadWise_Release_{uploaded_file.name}",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )

                except Exception as e:
                    # Critical Operation Failure Catch
                    log_error("UI Pipeline Error Caught", error=e)
                    progress_bar.empty()
                    status_box.error(f"❌ Automation Failure Caught: {str(e)}")
                    with st.expander("Show Detailed Error Log"):
                        st.code(traceback.format_exc(), language="python")

        except ValueError as e:
            # Extraction Failure Catch
            st.error(f"❌ Input Validation Failed: {str(e)}")
            st.warning("Please ensure the template follows the standardized ThreadWise formats, or that no required cells are left totally blank before proceeding.")

if __name__ == "__main__":
    main()
