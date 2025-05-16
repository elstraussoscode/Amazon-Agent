import streamlit as st

def render_configuration():
    """
    Render the configuration page for client settings
    """
    st.title("Client Configuration")
    
    # Get existing config or use defaults
    if 'client_config' not in st.session_state:
        st.session_state.client_config = {
            'client_name': 'Default Client',
            'is_market_leader': False,
            'has_large_inventory': False,
            'target_acos': 20.0
        }
    
    # Client information form
    with st.form("client_config_form"):
        st.subheader("Client Information")
        
        client_name = st.text_input(
            "Client Name", 
            value=st.session_state.client_config.get('client_name', 'Default Client')
        )
        
        # Client type options
        st.subheader("Client Type")
        col1, col2 = st.columns(2)
        
        with col1:
            is_market_leader = st.checkbox(
                "Market Leader with Brand Recognition", 
                value=st.session_state.client_config.get('is_market_leader', False),
                help="Select if client is a market leader with established brand recognition"
            )
        
        with col2:
            has_large_inventory = st.checkbox(
                "Large Inventory with Limited Budget", 
                value=st.session_state.client_config.get('has_large_inventory', False),
                help="Select if client has a large product selection but limited budget"
            )
        
        # Campaign targets
        st.subheader("Campaign Targets")
        
        # Recommendation based on selected options
        recommended_acos = 20.0  # Default
        if is_market_leader:
            recommended_acos = 8.0
        elif has_large_inventory:
            recommended_acos = 8.0
        
        target_acos = st.slider(
            "Target ACOS (%)", 
            min_value=5.0, 
            max_value=50.0, 
            value=st.session_state.client_config.get('target_acos', recommended_acos),
            step=0.5,
            help="Target Advertising Cost of Sale percentage"
        )
        
        # Advanced options
        with st.expander("Advanced Options"):
            keywords_min_clicks = st.number_input(
                "Minimum Clicks for Keyword Analysis", 
                min_value=1, 
                max_value=100, 
                value=st.session_state.client_config.get('keywords_min_clicks', 25),
                help="Minimum number of clicks before a keyword is analyzed for performance"
            )
            
            min_conversion_rate = st.slider(
                "Minimum Conversion Rate (%)", 
                min_value=1.0, 
                max_value=30.0, 
                value=st.session_state.client_config.get('min_conversion_rate', 10.0),
                step=0.5,
                help="Minimum conversion rate threshold for keywords"
            )
        
        # Submit button
        submitted = st.form_submit_button("Save Configuration")
        
        if submitted:
            # Update session state
            st.session_state.client_config = {
                'client_name': client_name,
                'is_market_leader': is_market_leader,
                'has_large_inventory': has_large_inventory,
                'target_acos': target_acos,
                'keywords_min_clicks': keywords_min_clicks,
                'min_conversion_rate': min_conversion_rate
            }
            
            st.success(f"Configuration saved for {client_name}")
    
    # Display current configuration
    if st.session_state.client_config:
        st.subheader("Current Configuration")
        
        config = st.session_state.client_config
        
        # Create a styled representation of the configuration
        st.info(f"""
        **Client:** {config.get('client_name', 'Not set')}
        
        **Target ACOS:** {config.get('target_acos', 20.0)}%
        
        **Client Type:**
        - Market Leader: {'✅' if config.get('is_market_leader', False) else '❌'}
        - Large Inventory: {'✅' if config.get('has_large_inventory', False) else '❌'}
        
        **Advanced Settings:**
        - Min. Clicks for Analysis: {config.get('keywords_min_clicks', 25)}
        - Min. Conversion Rate: {config.get('min_conversion_rate', 10.0)}%
        """) 