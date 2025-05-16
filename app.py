import streamlit as st
import pandas as pd
import os
from app.utils.excel_processor import process_amazon_report
from app.utils.optimizer import apply_optimization_rules
from app.components.dashboard import render_dashboard
from app.components.configuration import render_configuration
from app.utils.export_utils import generate_export_excel
from io import BytesIO

st.set_page_config(
    page_title="Amazon PPC Optimizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.sidebar.title("Amazon PPC Optimizer")
    
    # Initialize session state for page navigation if not already set
    if 'page' not in st.session_state:
        st.session_state.page = "Upload Report"
        
    # Navigation
    # Use st.session_state.page for consistent navigation after button clicks
    page_options = ["Upload Report", "Configuration", "Dashboard"]
    current_page_index = page_options.index(st.session_state.page) if st.session_state.page in page_options else 0
    
    # Update session state page based on sidebar selection
    # This should ideally be handled by making the selectbox directly control st.session_state.page
    # or by using a callback.
    # For simplicity, we read the selectbox and update if it differs from current session page.
    selected_page_from_sidebar = st.sidebar.selectbox(
        "Navigate", 
        page_options,
        index=current_page_index,
        key="navigation_selectbox" # Add a key for stability
    )
    if st.session_state.page != selected_page_from_sidebar:
        st.session_state.page = selected_page_from_sidebar
        st.experimental_rerun() # Rerun to reflect page change from sidebar

    active_page = st.session_state.page
    
    if active_page == "Upload Report":
        st.title("Upload Amazon PPC Report")
        
        with st.expander("Help with file upload", expanded=True):
            st.markdown("""
            ### Expected File Format
            Please upload an Amazon Bulk Sheet Excel file. The primary sheet for analysis should be identifiable 
            (e.g., named containing "Suchbegriff", "Search Term", or specifically "SP Bericht Suchbegriff").
            
            **Key columns expected for optimization** (names can vary, common German/English versions handled):
            - A column for **Keywords** (e.g., "Keyword-Text", "Keyword") - used for bid adjustments.
            - A column for **Customer Search Terms** (e.g., "Suchbegriff eines Kunden", "Customer Search Term") - used for analysis.
            - Columns for performance metrics: **Clicks**, **Spend**, Orders, Sales, CPC, etc.
            """)
        
        uploaded_file = st.file_uploader("Choose an Amazon Bulk Sheet (Excel)", type=["xlsx"])
        
        if uploaded_file is not None:
            temp_upload_dir = "temp_uploads"
            if not os.path.exists(temp_upload_dir):
                os.makedirs(temp_upload_dir)
            temp_upload_filepath = os.path.join(temp_upload_dir, uploaded_file.name)
            
            try:
                with open(temp_upload_filepath, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.session_state.temp_upload_filepath = temp_upload_filepath # Store for exporter
                
                with st.spinner("Processing Excel file..."):
                    # Update to handle new return values from process_amazon_report
                    processed_data = process_amazon_report(temp_upload_filepath)
                    
                    if processed_data[0] is None: # Check if processing failed (indicated by first element being None)
                        st.error("Failed to process the Excel file. Please check the error messages above and the file format.")
                        return

                    (
                        df_campaign, df_search_terms, 
                        original_search_terms_sheet_name, original_campaign_sheet_name,
                        identified_original_keyword_column, identified_original_bid_target_column,
                        all_original_sheet_names
                    ) = processed_data
                
                if df_search_terms is None or df_search_terms.empty:
                    st.error("Could not extract valid search terms data. Please check the file and selected sheet.")
                    return
                
                st.subheader("Preview of Campaign Data")
                if df_campaign is not None and not df_campaign.empty:
                    st.dataframe(df_campaign.head(), use_container_width=True)
                else:
                    st.warning("No campaign data found or processed.")
                
                st.subheader("Preview of Search Terms Data (Processed)")
                st.dataframe(df_search_terms.head(), use_container_width=True)
                    
                can_continue = True
                # Ensure essential columns for optimizer are present in the *processed* df_search_terms
                if 'keyword' not in df_search_terms.columns:
                    st.error("Processed data is missing the 'keyword' column. Cannot continue.")
                    can_continue = False
                if 'clicks' not in df_search_terms.columns or 'spend' not in df_search_terms.columns:
                    st.error("Processed data is missing 'clicks' or 'spend' columns. Cannot continue.")
                    can_continue = False
                
                if can_continue:
                    st.session_state.df_campaign = df_campaign
                    st.session_state.df_search_terms = df_search_terms
                    # Store original names for export
                    st.session_state.original_search_terms_sheet_name = original_search_terms_sheet_name
                    st.session_state.original_campaign_sheet_name = original_campaign_sheet_name
                    st.session_state.identified_original_keyword_column = identified_original_keyword_column
                    st.session_state.identified_original_bid_target_column = identified_original_bid_target_column
                    st.session_state.all_original_sheet_names = all_original_sheet_names
                    
                    if st.button("Run Optimization"):
                        with st.spinner("Applying optimization rules..."):
                            client_config = st.session_state.get('client_config', {
                                'is_market_leader': False, 'has_large_inventory': False,
                                'target_acos': 20.0, 'client_name': 'Default Client'
                            })
                            try:
                                optimization_results = apply_optimization_rules(
                                    st.session_state.df_campaign, 
                                    st.session_state.df_search_terms,
                                    client_config
                                )
                                st.session_state.optimization_results = optimization_results
                                st.success("Optimization completed successfully!")
                                st.session_state.page = "Dashboard" # Navigate to Dashboard
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error during optimization: {str(e)}")
                                import traceback
                                st.code(traceback.format_exc())
            except Exception as e:
                st.error(f"Error processing the uploaded file: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
            finally:
                # Clean up temp file if needed, or leave for export
                # For now, we leave it as its path is stored for export
                pass 
    
    elif active_page == "Configuration":
        render_configuration()
    
    elif active_page == "Dashboard":
        if 'optimization_results' in st.session_state:
            render_dashboard(st.session_state.optimization_results)
            
            # Add Export Button here or within render_dashboard
            if st.button("Prepare Export File"):
                if not st.session_state.get('identified_original_keyword_column') or \
                   not st.session_state.get('identified_original_bid_target_column'):
                    st.error("Cannot export: Original keyword or bid column names were not properly identified during upload. Please re-upload.")
                else:
                    with st.spinner("Generating export file..."):
                        export_file_bytes = generate_export_excel(
                            original_excel_path=st.session_state.temp_upload_filepath,
                            bid_changes=st.session_state.optimization_results.get('bid_changes', []),
                            search_terms_sheet_name=st.session_state.original_search_terms_sheet_name,
                            keyword_match_col_original_name=st.session_state.identified_original_keyword_column,
                            bid_update_col_original_name=st.session_state.identified_original_bid_target_column,
                            campaign_sheet_name=st.session_state.original_campaign_sheet_name,
                            all_original_sheet_names=st.session_state.all_original_sheet_names
                        )
                        if export_file_bytes:
                            st.session_state.export_file_bytes = export_file_bytes
                            st.success("Export file ready for download.")
                        else:
                            st.error("Failed to generate export file.")
            
            if 'export_file_bytes' in st.session_state and st.session_state.export_file_bytes:
                st.download_button(
                    label="Download Updated Report (.xlsx)",
                    data=st.session_state.export_file_bytes,
                    file_name="optimized_amazon_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                # Optionally clear after download to prevent re-downloading same data or to save memory
                # del st.session_state.export_file_bytes

        else:
            st.info("Please upload and optimize a report first to view the dashboard and export results.")
            if st.button("Go to Upload Page"):
                st.session_state.page = "Upload Report"
                st.experimental_rerun()

if __name__ == "__main__":
    main() 