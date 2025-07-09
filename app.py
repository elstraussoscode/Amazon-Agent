import streamlit as st
import pandas as pd
import os
from app.utils.excel_processor import process_amazon_report
from app.utils.optimizer import apply_optimization_rules
from app.components.dashboard import render_dashboard
from app.components.configuration import render_configuration
from app.utils.export_utils import generate_export_excel
from io import BytesIO
from app.utils.placement_adjuster import compute_placement_adjustments

st.set_page_config(
    page_title="Amazon PPC Optimizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.sidebar.title("Amazon PPC Optimierer")
    
    # Initialize session state for page navigation if not already set
    if 'page' not in st.session_state:
        st.session_state.page = "Upload Report"
        
    # Navigation
    # Use st.session_state.page for consistent navigation after button clicks
    page_options = ["Bericht hochladen", "Konfiguration", "Dashboard"]
    current_page_index = page_options.index(st.session_state.page) if st.session_state.page in page_options else 0
    
    # Update session state page based on sidebar selection
    # This should ideally be handled by making the selectbox directly control st.session_state.page
    # or by using a callback.
    # For simplicity, we read the selectbox and update if it differs from current session page.
    selected_page_from_sidebar = st.sidebar.selectbox(
        "Navigation", 
        page_options,
        index=current_page_index,
        key="navigation_selectbox" # Add a key for stability
    )
    if st.session_state.page != selected_page_from_sidebar:
        st.session_state.page = selected_page_from_sidebar
        st.rerun() # Rerun to reflect page change from sidebar

    active_page = st.session_state.page
    
    if active_page == "Bericht hochladen":
        st.title("Amazon-PPC-Bericht hochladen")
        
        with st.expander("Hilfe zum Datei-Upload", expanded=True):
            st.markdown("""
            ### Erwartetes Dateiformat
            Bitte lade eine Amazon Bulk-Sheet-Excel-Datei mit folgenden Arbeitsblättern hoch:
            
            **Erforderlich für Gebotsänderungen:**
            - **Sponsored Products-Kampagnen** – hier werden die Gebote angepasst
            
            **Optional für Analyse:**
            - **SP Bericht Suchbegriff** – dient nur zur Analyse von Keyword-Ausreißern (hoher ACOS, ACOS = 0, sehr niedriger ACOS)
            
            **Wichtige Spalten im Sheet „Sponsored Products-Kampagnen“:**
            - **Keywords** (z. B. „Keyword-Text“) – zum Abgleich und Anpassen der Gebote
            - **Gebote** (z. B. „Max. Gebot“, „CPC“) – werden aktualisiert
            - Leistungskennzahlen: **Klicks**, **Kosten**, **Bestellungen**, **Umsatz**, **ACOS** etc.
            
            Das System identifiziert Keyword-Ausreißer und passt die Gebote entsprechend an.
            """)
        
        uploaded_file = st.file_uploader("Bulk-Sheet auswählen (Excel)", type=["xlsx"])
        
        if uploaded_file is not None:
            temp_upload_dir = "temp_uploads"
            if not os.path.exists(temp_upload_dir):
                os.makedirs(temp_upload_dir)
            temp_upload_filepath = os.path.join(temp_upload_dir, uploaded_file.name)
            
            try:
                with open(temp_upload_filepath, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.session_state.temp_upload_filepath = temp_upload_filepath # Store for exporter
                
                with st.spinner("Excel-Datei verarbeiten..."):
                    # Update to handle new return values from process_amazon_report
                    processed_data = process_amazon_report(temp_upload_filepath)
                    
                    if processed_data[0] is None: # Check if processing failed (indicated by first element being None)
                        st.error("Datei konnte nicht verarbeitet werden. Bitte überprüfen Sie die Fehlermeldungen und das Dateiformat.")
                        return

                    (
                        df_campaign, df_search_terms, 
                        original_search_terms_sheet_name, original_campaign_sheet_name,
                        identified_original_keyword_column, identified_original_bid_target_column,
                        all_original_sheet_names
                    ) = processed_data
                
                if df_campaign is None or df_campaign.empty:
                    st.error("Konnte keine gültigen Kampagnendaten extrahieren. Bitte überprüfen Sie die Datei und stellen Sie sicher, dass das Blatt „Sponsored Products-Kampagnen“ existiert.")
                    return
                
                # --- Preview processed data ---
                st.subheader("Vorschau Kampagnendaten (Basis für Änderungen)")
                st.dataframe(df_campaign.head(), use_container_width=True)
                
                if df_search_terms is not None and not df_search_terms.empty:
                    st.subheader("Vorschau Suchbegriff-Daten (nur Analyse)")
                    st.dataframe(df_search_terms.head(), use_container_width=True)
                else:
                    st.warning("Kein Suchbegriff-Sheet gefunden. Analyse beschränkt sich auf Kampagnendaten.")
                    
                can_continue = True
                # Ensure essential columns for optimizer are present in the campaign data
                if 'keyword' not in df_campaign.columns:
                    st.error("Kampagnendaten fehlt die 'keyword' Spalte. Fortfahren nicht möglich.")
                    can_continue = False
                if 'clicks' not in df_campaign.columns or 'spend' not in df_campaign.columns:
                    st.error("Kampagnendaten fehlt die 'clicks' oder 'spend' Spalten. Fortfahren nicht möglich.")
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
                    
                    if st.button("Optimierung starten"):
                        with st.spinner("Optimierungsregeln anwenden..."):
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
                                # --- NEW: Calculate placement bid adjustments ---
                                try:
                                    placement_adjustments = compute_placement_adjustments(
                                        st.session_state.df_campaign,
                                        target_acos=float(client_config.get('target_acos', 20.0)) / 100 if client_config.get('target_acos', 20.0) > 1 else float(client_config.get('target_acos', 0.20))
                                    )
                                except Exception as e:
                                    placement_adjustments = []
                                    st.warning(f"Platzierungs-Anpassungen konnten nicht berechnet werden: {e}")
                                optimization_results['placement_adjustments'] = placement_adjustments

                                # Keyword classification
                                from app.utils.keyword_classifier import classify_keywords
                                keyword_perf = classify_keywords(st.session_state.df_campaign, target_acos=float(client_config.get('target_acos',20))/100)
                                optimization_results['keyword_performance'] = keyword_perf
                                st.session_state.optimization_results = optimization_results
                                st.success("Optimierung erfolgreich abgeschlossen!")
                                st.session_state.page = "Dashboard" # Navigate to Dashboard
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler während der Optimierung: {str(e)}")
                                import traceback
                                st.code(traceback.format_exc())
            except Exception as e:
                st.error(f"Fehler beim Verarbeiten der hochgeladenen Datei: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
            finally:
                # Clean up temp file if needed, or leave for export
                # For now, we leave it as its path is stored for export
                pass 
    
    elif active_page == "Konfiguration":
        render_configuration()
    
    elif active_page == "Dashboard":
        if 'optimization_results' in st.session_state:
            render_dashboard(st.session_state.optimization_results)
            
            # Add Export Button here or within render_dashboard
            if st.button("Export-Datei vorbereiten"):
                if not st.session_state.get('identified_original_keyword_column') or \
                   not st.session_state.get('identified_original_bid_target_column'):
                    st.error("Export nicht möglich: Original-Schlüsselwort oder Gebots-Spalten-Namen wurden während des Uploads nicht korrekt identifiziert. Bitte laden Sie erneut hoch.")
                else:
                    with st.spinner("Export-Datei generieren..."):
                        export_file_bytes = generate_export_excel(
                            original_excel_path=st.session_state.temp_upload_filepath,
                            bid_changes=st.session_state.optimization_results.get('bid_changes', []),
                            search_terms_sheet_name=st.session_state.original_search_terms_sheet_name,
                            keyword_match_col_original_name=st.session_state.identified_original_keyword_column,
                            bid_update_col_original_name=st.session_state.identified_original_bid_target_column,
                            campaign_sheet_name=st.session_state.original_campaign_sheet_name,
                            all_original_sheet_names=st.session_state.all_original_sheet_names,
                            placement_changes=st.session_state.optimization_results.get('placement_adjustments', [])
                        )
                        if export_file_bytes:
                            st.session_state.export_file_bytes = export_file_bytes
                            st.success("Export-Datei bereit für Download.")
                        else:
                            st.error("Export-Datei konnte nicht generiert werden.")
            
            if 'export_file_bytes' in st.session_state and st.session_state.export_file_bytes:
                st.download_button(
                    label="Aktualisierter Bericht herunterladen",
                    data=st.session_state.export_file_bytes,
                    file_name="optimized_amazon_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                # Optionally clear after download to prevent re-downloading same data or to save memory
                # del st.session_state.export_file_bytes

        else:
            st.info("Bitte laden Sie zuerst einen Bericht hoch und optimieren, um das Dashboard zu sehen und Ergebnisse zu exportieren.")
            if st.button("Zur Upload-Seite"):
                st.session_state.page = "Bericht hochladen"
                st.rerun()

if __name__ == "__main__":
    main() 