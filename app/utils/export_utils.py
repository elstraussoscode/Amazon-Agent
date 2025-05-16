import pandas as pd
from io import BytesIO
import streamlit as st # For potential logging or error display, though not strictly needed here

def generate_export_excel(original_excel_path: str,
                          bid_changes: list,
                          search_terms_sheet_name: str,
                          keyword_match_col_original_name: str,
                          bid_update_col_original_name: str,
                          campaign_sheet_name: str = None, # Optional: original campaign sheet name
                          all_original_sheet_names: list = None):
    """
    Generates an Excel file in memory with updated bids.

    Args:
        original_excel_path (str): Path to the originally uploaded Excel file.
        bid_changes (list): List of dictionaries with bid change information 
                              (must contain 'keyword' and 'new_bid').
        search_terms_sheet_name (str): The original name of the search terms sheet.
        keyword_match_col_original_name (str): Original name of the column to match keywords on.
        bid_update_col_original_name (str): Original name of the column where bids should be updated.
        campaign_sheet_name (str, optional): Original name of the campaign sheet, if any.
        all_original_sheet_names (list, optional): List of all original sheet names to preserve order and other sheets.

    Returns:
        BytesIO: Buffer containing the new Excel file, or None on failure.
    """
    if not original_excel_path:
        st.error("Export Error: Original Excel file path is missing.")
        return None
    if not search_terms_sheet_name:
        st.error("Export Error: Original search terms sheet name is missing.")
        return None
    if not keyword_match_col_original_name:
        st.error("Export Error: Original keyword column name for matching is missing.")
        return None
    if not bid_update_col_original_name:
        st.error("Export Error: Original bid column name for updating is missing.")
        return None

    try:
        xls = pd.ExcelFile(original_excel_path)
        
        # Use all_original_sheet_names if provided and valid, otherwise default to xls.sheet_names
        sheet_names_to_process = all_original_sheet_names if all_original_sheet_names and len(all_original_sheet_names) > 0 else xls.sheet_names
        
        sheets_data_processed = {}
        for name in sheet_names_to_process:
            if name in xls.sheet_names: # Ensure the sheet actually exists in the file
                 df_sheet = xls.parse(name)
                 # Convert object columns to string, except for known date/datetime (if any, not expected here for main sheets)
                 for col in df_sheet.select_dtypes(include=['object']).columns:
                     # A more robust check would be to see if a column is *intended* to be numeric but is object due to mixed types
                     # For now, a simple object -> str conversion for non-metrics is a safe default for this app's data.
                     # We specifically ensure the bid_update_col_original_name is numeric later if it's this sheet.
                     if name != search_terms_sheet_name or col != bid_update_col_original_name:
                        try:
                            # Attempt to convert to numeric first to see if it's mostly numbers being misinterpreted as object
                            # If it fails, then convert to string. This handles columns with mixed numbers and text better.
                            pd.to_numeric(df_sheet[col])
                            # If it is numeric, let pandas handle its type or Excel will do it.
                        except (ValueError, TypeError):
                            df_sheet[col] = df_sheet[col].astype(str).fillna('') # fillna for safety before str conversion
                 sheets_data_processed[name] = df_sheet
            else:
                 st.warning(f"Export Warning: Sheet '{name}' was listed but not found in the original file. It will be skipped.")

        if search_terms_sheet_name not in sheets_data_processed:
            st.error(f"Export Error: Search term sheet '{search_terms_sheet_name}' not found after loading Excel data.")
            return None

        df_to_update = sheets_data_processed[search_terms_sheet_name] # This is already a copy from the loop above

        if keyword_match_col_original_name not in df_to_update.columns:
            st.error(f"Export Error: Keyword match column '{keyword_match_col_original_name}' not found in sheet '{search_terms_sheet_name}'.")
            return None
        if bid_update_col_original_name not in df_to_update.columns:
            st.error(f"Export Error: Bid update column '{bid_update_col_original_name}' not found in sheet '{search_terms_sheet_name}'.")
            return None

        # Ensure the matching column is of string type for reliable matching
        df_to_update[keyword_match_col_original_name] = df_to_update[keyword_match_col_original_name].astype(str).fillna('')
        
        # Prepare bid update column to accept numeric data
        df_to_update[bid_update_col_original_name] = pd.to_numeric(df_to_update[bid_update_col_original_name], errors='coerce')

        updated_keywords_count = 0
        for change in bid_changes:
            keyword_to_match = str(change.get('keyword', '')).strip() # Add strip for robustness
            new_bid = change.get('new_bid')
            if new_bid is None: continue
            try:
                new_bid_float = float(new_bid)
            except (ValueError, TypeError):
                st.warning(f"Export Warning: Invalid new bid value '{new_bid}' for keyword '{keyword_to_match}'. Skipping.")
                continue
            
            # Match considering keyword_to_match could have different casing than in the sheet, make comparison case-insensitive if needed
            # For now, assuming original case sensitivity or that normalization handled it. If issues, make this case-insensitive.
            match_mask = df_to_update[keyword_match_col_original_name].str.strip() == keyword_to_match
            match_indices = df_to_update[match_mask].index
            
            if not match_indices.empty:
                df_to_update.loc[match_indices, bid_update_col_original_name] = new_bid_float
                updated_keywords_count += len(match_indices)
        
        st.info(f"Export Info: Updated bids for {updated_keywords_count} rows in sheet '{search_terms_sheet_name}'.")
        sheets_data_processed[search_terms_sheet_name] = df_to_update # Put the updated df back

        output_buffer = BytesIO()
        with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
            for sheet_name_to_write, df_data in sheets_data_processed.items():
                df_data.to_excel(writer, sheet_name=sheet_name_to_write, index=False)
        
        output_buffer.seek(0)
        return output_buffer

    except FileNotFoundError:
        st.error(f"Export Error: Original Excel file not found at '{original_excel_path}'.")
        return None
    except Exception as e:
        st.error(f"Export Error: An unexpected error occurred: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None 