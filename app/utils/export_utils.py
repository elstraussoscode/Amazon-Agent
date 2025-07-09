import pandas as pd
from io import BytesIO
import streamlit as st # For potential logging or error display, though not strictly needed here

def generate_export_excel(original_excel_path: str,
                          bid_changes: list,
                          search_terms_sheet_name: str,
                          keyword_match_col_original_name: str,
                          bid_update_col_original_name: str,
                          campaign_sheet_name: str = None, # Now required: original campaign sheet name
                          all_original_sheet_names: list = None,
                          placement_changes: list = None):
    """
    Generates an Excel file in memory with placement adjustments only.
    
    NOTE: Keyword bid updates have been disabled per user request.
    Only placement (Platzierung) adjustments will be applied to the exported file.

    Args:
        original_excel_path (str): Path to the originally uploaded Excel file.
        bid_changes (list): List of dictionaries with bid change information (IGNORED - keyword updates disabled).
        search_terms_sheet_name (str): The original name of the search terms sheet (for analysis reference).
        keyword_match_col_original_name (str): Original name of the column to match keywords on in campaign sheet (IGNORED).
        bid_update_col_original_name (str): Original name of the column where bids should be updated (IGNORED).
        campaign_sheet_name (str, required): Original name of the campaign sheet where changes are made.
        all_original_sheet_names (list, optional): List of all original sheet names to preserve order and other sheets.
        placement_changes (list, optional): List of placement adjustment changes to apply.

    Returns:
        BytesIO: Buffer containing the new Excel file with placement adjustments only, or None on failure.
    """
    if not original_excel_path:
        st.error("Export Error: Original Excel file path is missing.")
        return None
    if not campaign_sheet_name:
        st.error("Export Error: Campaign sheet name is required for making bid changes.")
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
        
        sheets_data = {}
        for name in sheet_names_to_process:
            if name in xls.sheet_names: # Ensure the sheet actually exists in the file
                 sheets_data[name] = xls.parse(name)
            else:
                 st.warning(f"Export Warning: Sheet '{name}' was listed but not found in the original file. It will be skipped.")

        if campaign_sheet_name not in sheets_data:
            st.error(f"Export Error: Campaign sheet '{campaign_sheet_name}' not found in the loaded Excel data.")
            return None

        df_to_update = sheets_data[campaign_sheet_name].copy() # Work on campaign sheet copy

        if keyword_match_col_original_name not in df_to_update.columns:
            st.error(f"Export Error: Keyword match column '{keyword_match_col_original_name}' not found in sheet '{campaign_sheet_name}'. Available: {df_to_update.columns.tolist()}")
            return None
        if bid_update_col_original_name not in df_to_update.columns:
            st.error(f"Export Error: Bid update column '{bid_update_col_original_name}' not found in sheet '{campaign_sheet_name}'. Available: {df_to_update.columns.tolist()}")
            return None

        # --- Clean Keyword Match Column ---------------------------------------------------
        # Convert to string **after** filling NaNs so we do not get the literal string "nan".
        df_to_update[keyword_match_col_original_name] = (
            df_to_update[keyword_match_col_original_name]
            .fillna("")          # real NaNs → blank strings
            .astype(str)          # keep original text
        )

        # Remove any leftover literal "nan" / "None" strings that might already exist
        df_to_update[keyword_match_col_original_name].replace(
            to_replace=["nan", "NaN", "None"], value="", inplace=True
        )
        
        # Prepare bid update column to accept numeric data, preserving existing numbers
        df_to_update[bid_update_col_original_name] = pd.to_numeric(df_to_update[bid_update_col_original_name], errors='coerce')

        # Ensure an 'Operation' column exists (Amazon bulksheet expects this in column C).
        # If not present, insert it as the third column (index 2) and default to empty strings.
        if 'Operation' not in df_to_update.columns:
            df_to_update.insert(2, 'Operation', '')

        updated_keywords_count = 0
        updated_placements_count = 0
        
        # --- KEYWORD BID UPDATES DISABLED ---
        # Keyword bid updates have been disabled per user request.
        # Only placement adjustments will be included in the export.
        st.info("ℹ️ Keyword bid updates are disabled. Only placement adjustments will be exported.")
        
        # ------------------- Apply placement changes ----------------------------
        if placement_changes:
            if 'Platzierung' in df_to_update.columns and 'Prozentsatz' in df_to_update.columns:
                for pl_change in placement_changes:
                    camp_id = pl_change.get('campaign_id')
                    placement_label = pl_change.get('placement')
                    new_pct = pl_change.get('recommended_adjust_pct')

                    try:
                        new_pct_val = float(new_pct)
                    except (ValueError, TypeError):
                        continue

                    # Ensure we only update placement adjustment rows, not keyword rows
                    if 'Entität' in df_to_update.columns:
                        entity_col = 'Entität'
                    elif 'Entity' in df_to_update.columns:
                        entity_col = 'Entity'
                    else:
                        entity_col = None
                    
                    if entity_col:
                        mask_pl = (
                            (df_to_update['Kampagnen-ID'] == camp_id) &
                            (df_to_update['Platzierung'] == placement_label) &
                            (df_to_update[entity_col].astype(str).str.lower() == 'gebotsanpassung')
                        )
                    else:
                        # Fallback: if no entity column, use original logic but with warning
                        mask_pl = (
                            (df_to_update['Kampagnen-ID'] == camp_id) &
                            (df_to_update['Platzierung'] == placement_label)
                        )
                        st.warning("⚠️ No Entity column found. Placement updates may affect unintended rows.")
                    idxs = df_to_update[mask_pl].index
                    if not idxs.empty:
                        df_to_update.loc[idxs, 'Prozentsatz'] = new_pct_val
                        df_to_update.loc[idxs, 'Operation'] = 'Update'
                        updated_placements_count += len(idxs)

            # else: silently ignore if columns missing

        sheets_data[campaign_sheet_name] = df_to_update

        # Show export summary
        if updated_placements_count > 0:
            st.success(f"✅ Export erfolgreich: {updated_placements_count} Platzierungs-Anpassungen wurden aktualisiert.")
        else:
            st.warning("⚠️ Keine Platzierungs-Anpassungen gefunden oder angewendet.")

        output_buffer = BytesIO()
        with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
            for sheet_name_to_write in sheet_names_to_process:
                if sheet_name_to_write in sheets_data: # Check if sheet was loaded
                    sheets_data[sheet_name_to_write].to_excel(writer, sheet_name=sheet_name_to_write, index=False)
        
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