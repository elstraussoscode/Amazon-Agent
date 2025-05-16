import pandas as pd
import streamlit as st

def process_amazon_report(file_path):
    """
    Process Amazon Bulk Sheet Excel file and extract campaign and search term data.
    Also identifies original sheet and column names for potential export.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        tuple: (
            df_campaign_processed, 
            df_search_terms_processed, 
            original_search_terms_sheet_name, 
            original_campaign_sheet_name,
            identified_original_keyword_column,  // e.g., "Keyword-Text"
            identified_original_bid_target_column // e.g., "CPC" or "Kosten pro Klick"
        )
    """
    try:
        xls = pd.ExcelFile(file_path)
        all_sheet_names = xls.sheet_names
        st.info(f"Sheets found in Excel file: {', '.join(all_sheet_names)}")

        original_search_terms_sheet_name = None
        original_campaign_sheet_name = None

        # --- Sheet Identification ---
        if "SP Bericht Suchbegriff" in all_sheet_names:
            original_search_terms_sheet_name = "SP Bericht Suchbegriff"
            st.success(f"Found the specified 'SP Bericht Suchbegriff' sheet!")
        else:
            for sheet in all_sheet_names:
                if "Suchbegriff" in sheet or "Search Term" in sheet or "SP Bericht" in sheet:
                    original_search_terms_sheet_name = sheet
                    break
        
        for sheet in all_sheet_names:
            if "Kampagne" in sheet or "Campaign" in sheet or "Sponsored Products" in sheet:
                original_campaign_sheet_name = sheet
                break

        if not original_search_terms_sheet_name:
            st.warning("Could not find 'SP Bericht Suchbegriff' or any search terms sheet. Please select manually.")
            original_search_terms_sheet_name = st.selectbox(
                "Select Search Terms Sheet", options=all_sheet_names, index=0 if all_sheet_names else None, key="select_search_sheet_import_dtype"
            )
        st.info(f"Using '{original_search_terms_sheet_name}' for search terms data")

        # --- Load Raw Data with dtype=str for Search Terms, then selectively convert numerics ---
        # Load all columns as string first to preserve text-like IDs etc.
        df_search_terms_raw = pd.read_excel(file_path, sheet_name=original_search_terms_sheet_name, dtype=str)
        raw_search_term_columns = list(df_search_terms_raw.columns) # Get original column names

        # Identify columns that should be numeric BEFORE normalization/mapping
        # These are common metric column names in German or English reports
        # We'll try to convert these based on their original names.
        potential_numeric_cols_search_terms_original_names = [
            'Klicks', 'Clicks', 'Impressionen', 'Impressions',
            'Ausgaben', 'Spend', 'Umsatz', 'Sales', 'Verkäufe', # Verkäufe often means revenue/sales
            'Bestellungen', 'Orders',
            'CPC', 'Kosten pro Klick',
            'Conversion Rate', 'Konversionsrate',
            'ACoS', 'Ziel-ACoS' # and similar for ACOS
            # Add other known original numeric column names if necessary
        ]

        for orig_col_name in raw_search_term_columns:
            if orig_col_name in potential_numeric_cols_search_terms_original_names:
                # Coerce errors: if a value can't be converted, it becomes NaN
                df_search_terms_raw[orig_col_name] = pd.to_numeric(df_search_terms_raw[orig_col_name], errors='coerce')
                st.info(f"Converted column '{orig_col_name}' to numeric.")
        
        # --- Identify Original Key Columns for Export (after potential numeric conversion) ---
        column_mappings_search_terms = {
            'suchbegriff': 'customer_search_term', 'suchbegriff eines kunden': 'customer_search_term', 'customer search term': 'customer_search_term',
            'keyword-text': 'keyword', 'keyword text': 'keyword', 'keyword': 'keyword',
            'klicks': 'clicks', 'impressionen': 'impressions', 'ausgaben': 'spend', 'verkäufe': 'sales', 'umsatz':'sales',
            'bestellungen': 'orders', 'acos': 'acos', 'conversion rate': 'conversion_rate',
            'konversionsrate': 'conversion_rate', 'cpc': 'cpc', 'kosten pro klick': 'cpc', 'roas': 'roas'
        }

        identified_original_keyword_column = None
        identified_original_bid_target_column = None

        preferred_keyword_keys_normalized = ['keyword-text', 'keyword_text', 'keyword']
        for orig_col_name in raw_search_term_columns:
            norm_col = str(orig_col_name).lower().strip().replace(' ', '_') # Ensure orig_col_name is string for .lower()
            if norm_col in preferred_keyword_keys_normalized and column_mappings_search_terms.get(norm_col) == 'keyword':
                identified_original_keyword_column = orig_col_name
                break
        if not identified_original_keyword_column:
             for orig_col_name in raw_search_term_columns:
                norm_col = str(orig_col_name).lower().strip().replace(' ', '_')
                if column_mappings_search_terms.get(norm_col) == 'keyword':
                    identified_original_keyword_column = orig_col_name
                    break
        
        preferred_cpc_keys_normalized = ['kosten_pro_klick', 'cpc']
        for orig_col_name in raw_search_term_columns:
            norm_col = str(orig_col_name).lower().strip().replace(' ', '_')
            if norm_col in preferred_cpc_keys_normalized and column_mappings_search_terms.get(norm_col) == 'cpc':
                identified_original_bid_target_column = orig_col_name
                break
        if not identified_original_bid_target_column:
            for orig_col_name in raw_search_term_columns:
                norm_col = str(orig_col_name).lower().strip().replace(' ', '_')
                if column_mappings_search_terms.get(norm_col) == 'cpc':
                    identified_original_bid_target_column = orig_col_name
                    break
        
        # --- Prepare DataFrames for Processing ---
        df_search_terms_processed = df_search_terms_raw.copy()
        
        if original_campaign_sheet_name:
            df_campaign_raw = pd.read_excel(file_path, sheet_name=original_campaign_sheet_name, dtype=str)
            raw_campaign_columns = list(df_campaign_raw.columns)
            st.info(f"Using '{original_campaign_sheet_name}' for campaign data. Original columns: {raw_campaign_columns}")
            
            potential_numeric_cols_campaign_original_names = [
                'Tagesbudget', 'Daily Budget', 'Max. Gebot', 'Max Bid'
                # Add other known original campaign numeric columns if necessary
            ]
            for orig_col_name in raw_campaign_columns:
                if orig_col_name in potential_numeric_cols_campaign_original_names:
                    df_campaign_raw[orig_col_name] = pd.to_numeric(df_campaign_raw[orig_col_name], errors='coerce')
                    # st.info(f"Campaign: Converted column '{orig_col_name}' to numeric.")
            
            df_campaign_processed = df_campaign_raw.copy()
            if not df_campaign_processed.empty:
                 df_campaign_processed.columns = [str(col).lower().strip().replace(' ', '_') for col in df_campaign_processed.columns]
        else:
            df_campaign_processed = pd.DataFrame(columns=['campaign_name', 'daily_budget', 'status'])
            st.warning("No campaign sheet found. Created a placeholder campaign dataframe.")

        st.info(f"Search terms sheet original columns (after initial numeric conversion): {', '.join(df_search_terms_processed.columns)}")
        # Normalize column names AFTER selective numeric conversion and original name identification
        df_search_terms_processed.columns = [str(col).lower().strip().replace(' ', '_') for col in df_search_terms_processed.columns]
        
        # --- Column Mapping for Processing ---
        column_mappings_campaign_proc = {
            'kampagne': 'campaign_name', 'kampagnenname': 'campaign_name', 'tagesbudget': 'daily_budget',
            'status': 'status', 'gebotstyp': 'bidding_strategy', 'anzeigengruppe': 'ad_group_name',
            'anzeigengruppenname': 'ad_group_name', 'max._gebot': 'max_bid', 'maximales_gebot': 'max_bid',
            'campaign_id': 'campaign_id', 'kampagnen-id': 'campaign_id', # Assuming campaign IDs should be kept as strings
            'ad_group_id': 'ad_group_id', 'anzeigengruppen-id': 'ad_group_id' # Assuming ad group IDs should be kept as strings
        }
        # Search terms mapping is already defined as column_mappings_search_terms

        if not df_campaign_processed.empty:
            df_campaign_processed = rename_columns_for_processing(df_campaign_processed, column_mappings_campaign_proc)
        df_search_terms_processed = rename_columns_for_processing(df_search_terms_processed, column_mappings_search_terms)
        
        # --- Handle Missing Required Columns for Processing ---
        required_search_cols_proc = ['keyword', 'customer_search_term', 'clicks', 'spend']
        missing_cols_proc = [col for col in required_search_cols_proc if col not in df_search_terms_processed.columns]
        
        if missing_cols_proc:
            st.warning(f"Missing required columns for processing after mapping: {', '.join(missing_cols_proc)}")
            if 'keyword' in missing_cols_proc and identified_original_keyword_column:
                 # If 'keyword' is missing but we know the original, try to map it again based on its normalized original name
                 norm_orig_kw_col = str(identified_original_keyword_column).lower().strip().replace(' ', '_')
                 if norm_orig_kw_col in df_search_terms_processed.columns and norm_orig_kw_col != 'keyword':
                     df_search_terms_processed.rename(columns={norm_orig_kw_col: 'keyword'}, inplace=True)
                     if 'keyword' in missing_cols_proc: missing_cols_proc.remove('keyword')
                     st.info(f"Re-mapped '{norm_orig_kw_col}' to 'keyword' for processing.")
            if 'customer_search_term' in missing_cols_proc:
                 # Similar logic for customer_search_term if needed for processing, though less critical for *bid export*
                 pass # Add user selection if customer_search_term is vital and missing

            for col in missing_cols_proc: # Handle other missing like clicks, spend
                if col in ['clicks', 'spend', 'sales', 'orders']:
                    df_search_terms_processed[col] = 0
                elif col in ['keyword', 'customer_search_term']: # If still missing, use empty string
                     df_search_terms_processed[col] = ""
        
        # Final check for export-critical original columns
        if not identified_original_keyword_column:
            st.error("The primary KEYWORD column for matching bids could not be identified. Export might not work correctly.")
        if not identified_original_bid_target_column:
            st.error("The BID/CPC column for updating bids could not be identified. Export might not work correctly.")


        # --- Calculate Derived Metrics if Missing (ACOS, Conversion Rate) ---
        if 'conversion_rate' not in df_search_terms_processed.columns and 'orders' in df_search_terms_processed.columns and 'clicks' in df_search_terms_processed.columns:
            # Ensure clicks and orders are numeric before division
            df_search_terms_processed['orders'] = pd.to_numeric(df_search_terms_processed['orders'], errors='coerce').fillna(0)
            df_search_terms_processed['clicks'] = pd.to_numeric(df_search_terms_processed['clicks'], errors='coerce').fillna(0)
            df_search_terms_processed['conversion_rate'] = (df_search_terms_processed['orders'] / df_search_terms_processed['clicks'].replace(0, float('nan'))) * 100
        if 'acos' not in df_search_terms_processed.columns and 'spend' in df_search_terms_processed.columns and 'sales' in df_search_terms_processed.columns:
            df_search_terms_processed['spend'] = pd.to_numeric(df_search_terms_processed['spend'], errors='coerce').fillna(0)
            df_search_terms_processed['sales'] = pd.to_numeric(df_search_terms_processed['sales'], errors='coerce').fillna(0)
            df_search_terms_processed['acos'] = (df_search_terms_processed['spend'] / df_search_terms_processed['sales'].replace(0, float('nan'))) * 100
        
        st.success(f"Processed search terms data columns: {', '.join(df_search_terms_processed.columns)}")
        
        return (
            df_campaign_processed, df_search_terms_processed, 
            original_search_terms_sheet_name, original_campaign_sheet_name,
            identified_original_keyword_column, identified_original_bid_target_column,
            all_sheet_names # Pass all original sheet names for preserving order/all sheets
        )
        
    except Exception as e:
        st.error(f"Error processing Excel file: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        # Return None for all expected values on error to allow graceful failure upstream
        return None, None, None, None, None, None, None

def rename_columns_for_processing(df, mapping):
    renamed_df = df.copy()
    current_columns = list(renamed_df.columns) # Operate on a copy of column names
    new_column_names = {} # To avoid direct modification issues during iteration

    for col_original in current_columns:
        col_lower_normalized = str(col_original).lower().strip().replace(' ', '_') # Ensure str before lower
        if col_lower_normalized in mapping:
            desired_new_name = mapping[col_lower_normalized]
            # Only rename if the new name isn't already taken by another original column
            # or if it's a direct self-map (col_original maps to itself essentially)
            if desired_new_name not in new_column_names.values() or new_column_names.get(col_original) == desired_new_name:
                 new_column_names[col_original] = desired_new_name
            # If desired_new_name is already a target for a *different* original column, prioritize first mapping
            # This simple approach might need refinement for complex conflicts, but good for now.

    # Apply renames from the collected map
    # This handles cases where multiple original columns might map to the same new_name
    # (e.g., 'keyword' and 'keyword text' both map to 'keyword') - the last one in mapping usually wins if not careful.
    # A more robust way is to ensure mapping keys are unique or prioritize.
    # For now, directly use the rename method with the collected new names.
    # Need to be careful if df.columns contains non-string types, hence the str() in normalization.
    final_rename_map = {orig: new for orig, new in new_column_names.items() if orig in renamed_df.columns}
    renamed_df.rename(columns=final_rename_map, inplace=True)
    return renamed_df 