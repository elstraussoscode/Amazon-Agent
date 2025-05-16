import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any

def render_dashboard(optimization_results: Dict[str, Any]):
    """
    Render the dashboard showing optimization results
    
    Args:
        optimization_results (dict): The optimization results from LangGraph workflow
    """
    st.title("Optimization Results Dashboard")
    
    # Extract data from results
    keyword_changes = optimization_results.get("keyword_changes", [])
    bid_changes = optimization_results.get("bid_changes", [])
    summary = optimization_results.get("summary", {})
    
    # Create metrics row - Updated for Bids Increased/Decreased
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Keywords Analyzed", 
            f"{summary.get('total_keywords_analyzed', 0)}"
        )
    
    with col2:
        st.metric(
            "Keywords to Pause",
            f"{summary.get('keywords_to_pause', 0)}",
            # delta=-summary.get('keywords_to_pause', 0), # Delta might be confusing here
            # delta_color="inverse"
        )
    
    with col3:
        st.metric(
            "Bids Increased",
            f"{summary.get('bids_to_increase', 0)}"
        )
    
    with col4:
        st.metric(
            "Bids Decreased",
            f"{summary.get('bids_to_decrease', 0)}"
        )
    
    estimated_acos_reduction = summary.get('estimated_impact', {}).get('projected_acos_reduction', 0)
    with col5:
        st.metric(
            "Est. ACOS Reduction",
            f"{estimated_acos_reduction:.2f}%",
            delta=f"{-estimated_acos_reduction:.2f}%" if estimated_acos_reduction != 0 else None, # Show negative delta for reduction
            delta_color="inverse" # Red for negative delta means good (reduction)
        )
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Overview", 
        "Keyword Changes", 
        "Bid Adjustments",
        "AI Recommendations"
    ])
    
    with tab1:
        render_overview_tab(optimization_results)
    
    with tab2:
        render_keyword_changes_tab(keyword_changes)
    
    with tab3:
        render_bid_changes_tab(bid_changes)
    
    with tab4:
        render_recommendations_tab(summary.get('general_recommendations', []))


def render_overview_tab(optimization_results: Dict[str, Any]):
    """Render the overview tab with summary charts"""
    summary = optimization_results.get("summary", {})
    
    st.subheader("Performance Impact")
    
    # Create columns for charts
    col1, col2 = st.columns(2)
    
    # Keyword actions pie chart
    with col1:
        keyword_data = {
            'Action': ['Pause', 'Keep'],
            'Count': [
                summary.get('keywords_to_pause', 0),
                summary.get('keywords_to_keep', 0)
            ]
        }
        df_keyword_pie = pd.DataFrame(keyword_data)
        
        if df_keyword_pie['Count'].sum() > 0:
            fig = px.pie(
                df_keyword_pie, 
                values='Count', 
                names='Action',
                title='Keyword Actions',
                color='Action',
                color_discrete_map={'Pause': '#FF4B4B', 'Keep': '#36A2EB'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No keyword data available")
    
    # Bid adjustments pie chart
    with col2:
        bid_data = {
            'Action': ['Increase', 'Decrease'],
            'Count': [
                summary.get('bids_to_increase', 0),
                summary.get('bids_to_decrease', 0)
            ]
        }
        df_bid_pie = pd.DataFrame(bid_data)
        
        if df_bid_pie['Count'].sum() > 0:
            fig = px.pie(
                df_bid_pie, 
                values='Count', 
                names='Action',
                title='Bid Adjustments',
                color='Action',
                color_discrete_map={'Increase': '#4BC0C0', 'Decrease': '#FFCD56'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No bid adjustment data available")
    
    # Cost savings
    st.subheader("Estimated Cost Savings")
    
    cost_saving = summary.get('estimated_impact', {}).get('cost_saving', 0)
    efficiency_improvement = summary.get('estimated_impact', {}).get('efficiency_improvement', 0)
    
    if cost_saving > 0 or efficiency_improvement > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Estimated Cost Savings",
                f"${cost_saving:.2f}",
                delta=f"${cost_saving:.2f}",
                delta_color="inverse"
            )
        
        with col2:
            st.metric(
                "Efficiency Improvement",
                f"{efficiency_improvement:.2f}%",
                delta=f"{efficiency_improvement:.2f}%"
            )
            
        # Add a gauge chart for ACOS reduction
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = summary.get('estimated_impact', {}).get('projected_acos_reduction', 0),
            title = {'text': "Projected ACOS Reduction (%)"},
            delta = {'reference': 0},
            gauge = {
                'axis': {'range': [None, 20]},
                'bar': {'color': "#36A2EB"},
                'steps': [
                    {'range': [0, 5], 'color': "#FFCD56"},
                    {'range': [5, 10], 'color': "#4BC0C0"},
                    {'range': [10, 20], 'color': "#FF4B4B"}
                ]
            }
        ))
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No cost savings data available")


def render_keyword_changes_tab(keyword_changes):
    """Render the keyword changes tab with detailed tables"""
    st.subheader("Keyword Optimization Details")
    
    if not keyword_changes:
        st.info("No keyword changes to display")
        return
    
    # Create DataFrame for display
    df_keywords = pd.DataFrame(keyword_changes)
    
    # Split into pause and keep
    if 'action' in df_keywords.columns:
        df_pause = df_keywords[df_keywords['action'] == 'pause']
        df_keep = df_keywords[df_keywords['action'] == 'keep']
        
        st.write(f"Total keywords: {len(df_keywords)}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Keywords to Pause")
            if not df_pause.empty:
                # Extract metrics from original_data
                df_pause_display = df_pause.copy()
                for idx, row in df_pause.iterrows():
                    if 'original_data' in row and isinstance(row['original_data'], dict):
                        for metric, value in row['original_data'].items():
                            df_pause_display.at[idx, metric] = value
                
                # Select columns to display
                display_cols = ['keyword', 'customer_search_term', 'reason', 'clicks', 'orders', 'acos', 'conversion_rate']
                display_cols = [col for col in display_cols if col in df_pause_display.columns]
                
                # Rename columns for better display
                if 'customer_search_term' in display_cols:
                    df_pause_display = df_pause_display.rename(columns={
                        'keyword': 'Campaign Keyword',
                        'customer_search_term': 'Customer Search Term'
                    })
                    display_cols = ['Campaign Keyword' if col == 'keyword' else 
                                  'Customer Search Term' if col == 'customer_search_term' else 
                                  col for col in display_cols]
                
                st.dataframe(df_pause_display[display_cols], use_container_width=True)
            else:
                st.info("No keywords to pause")
        
        with col2:
            st.subheader("Top Performing Keywords")
            if not df_keep.empty:
                # Extract metrics from original_data
                df_keep_display = df_keep.copy()
                for idx, row in df_keep.iterrows():
                    if 'original_data' in row and isinstance(row['original_data'], dict):
                        for metric, value in row['original_data'].items():
                            df_keep_display.at[idx, metric] = value
                
                # Select columns to display
                display_cols = ['keyword', 'customer_search_term', 'reason', 'clicks', 'orders', 'acos', 'conversion_rate']
                display_cols = [col for col in display_cols if col in df_keep_display.columns]
                
                # Rename columns for better display
                if 'customer_search_term' in display_cols:
                    df_keep_display = df_keep_display.rename(columns={
                        'keyword': 'Campaign Keyword',
                        'customer_search_term': 'Customer Search Term'
                    })
                    display_cols = ['Campaign Keyword' if col == 'keyword' else 
                                  'Customer Search Term' if col == 'customer_search_term' else 
                                  col for col in display_cols]
                
                # Sort by best performance (lowest ACOS)
                if 'acos' in df_keep_display.columns:
                    df_keep_display = df_keep_display.sort_values('acos')
                
                st.dataframe(df_keep_display[display_cols], use_container_width=True)
            else:
                st.info("No keywords to keep")
    else:
        st.dataframe(df_keywords)


def render_bid_changes_tab(bid_changes):
    """Render the bid changes tab with detailed tables"""
    st.subheader("Bid Adjustment Details")
    
    if not bid_changes:
        st.info("No bid changes to display")
        return
    
    # Create DataFrame for display
    df_bids = pd.DataFrame(bid_changes)
    
    # Add customer search term if available
    if 'customer_search_term' in df_bids.columns:
        # Rename columns for better display
        df_bids = df_bids.rename(columns={
            'keyword': 'Campaign Keyword',
            'customer_search_term': 'Customer Search Term',
            'current_bid': 'Current Bid',
            'new_bid': 'New Bid',
            'change_percentage': 'Change %'
        })
        
        # Format display columns
        display_cols = [
            'Campaign Keyword', 
            'Customer Search Term', 
            'Current Bid', 
            'New Bid', 
            'Change %', 
            'reason'
        ]
        display_cols = [col for col in display_cols if col in df_bids.columns]
    else:
        # Use original column names
        display_cols = ['keyword', 'current_bid', 'new_bid', 'change_percentage', 'reason']
        display_cols = [col for col in display_cols if col in df_bids.columns]
    
    # Split into increases and decreases
    if 'Change %' in df_bids.columns:
        change_col = 'Change %'
    else:
        change_col = 'change_percentage'
        
    if change_col in df_bids.columns:
        df_increases = df_bids[df_bids[change_col] > 0]
        df_decreases = df_bids[df_bids[change_col] < 0]
    
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Bid Increases")
            if not df_increases.empty:
                st.dataframe(df_increases[display_cols], use_container_width=True)
            else:
                st.info("No bid increases to display")
        
        with col2:
            st.subheader("Bid Decreases")
            if not df_decreases.empty:
                st.dataframe(df_decreases[display_cols], use_container_width=True)
            else:
                st.info("No bid decreases to display")
    else:
        # Just show everything in one table if change column not found
        st.dataframe(df_bids, use_container_width=True)


def render_recommendations_tab(recommendations):
    """Render the AI recommendations tab"""
    st.subheader("AI-Powered Recommendations")
    
    if not recommendations:
        st.info("No AI recommendations available")
        return
    
    for i, rec in enumerate(recommendations, 1):
        st.markdown(f"**{i}. {rec}**")
    
    # Add explanation
    st.markdown("---")
    st.markdown("""
    **About these recommendations:**
    
    These AI-powered recommendations are generated based on analysis of your campaign data and the optimization changes. 
    They are meant to complement the automated changes with strategic insights to further improve your PPC performance.
    """) 