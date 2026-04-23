def display_properties_professionally(properties, market_analysis, property_valuations, total_properties):
    """Display properties in a clean, professional UI using Streamlit components"""

    # Header with key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Properties Found", total_properties)
    with col2:
        # Calculate average price
        prices = []
        for p in properties:
            price_str = p.get('price', '') if isinstance(p, dict) else getattr(p, 'price', '')
            if price_str and price_str != 'Price not available':
                try:
                    price_num = ''.join(filter(str.isdigit, str(price_str)))
                    if price_num:
                        prices.append(int(price_num))
                except:
                    pass
        avg_price = f"${sum(prices) // len(prices):,}" if prices else "N/A"
        st.metric("Average Price", avg_price)
    with col3:
        types = {}
        for p in properties:
            t = p.get('property_type', 'Unknown') if isinstance(p, dict) else getattr(p, 'property_type', 'Unknown')
            types[t] = types.get(t, 0) + 1
        most_common = max(types.items(), key=lambda x: x[1])[0] if types else "N/A"
        st.metric("Most Common Type", most_common)

    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["🏠 Properties", "📊 Market Analysis", "💰 Valuations"])

    with tab1:
        for i, prop in enumerate(properties, 1):
            # Extract property data
            data = {k: prop.get(k, '') if isinstance(prop, dict) else getattr(prop, k, '') 
                   for k in ['address', 'price', 'property_type', 'bedrooms', 'bathrooms', 'square_feet', 'description', 'listing_url']}

            with st.container():
                # Property header with number and price
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"#{i} 🏠 {data['address']}")
                with col2:
                    st.metric("Price", data['price'])

                # Property details with right-aligned button
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.markdown(f"**Type:** {data['property_type']}")
                    st.markdown(f"**Beds/Baths:** {data['bedrooms']}/{data['bathrooms']}")
                    st.markdown(f"**Area:** {data['square_feet']}")
                with col2:
                    with st.expander("💰 Investment Analysis"):
                        # Extract property-specific valuation from the full analysis
                        property_valuation = extract_property_valuation(property_valuations, i, data['address'])
                        if property_valuation:
                            st.markdown(property_valuation)
                        else:
                            st.info("Investment analysis not available for this property")
                with col3:
                    if data['listing_url'] and data['listing_url'] != '#':
                        st.markdown(
                            f"""
                            <div style="height: 100%; display: flex; align-items: center; justify-content: flex-end;">
                                <a href="{data['listing_url']}" target="_blank" 
                                   style="text-decoration: none; padding: 0.5rem 1rem; 
                                   background-color: #0066cc; color: white; 
                                   border-radius: 6px; font-size: 0.9em; font-weight: 500;">
                                    Property Link
                                </a>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                st.divider()

    with tab2:
        st.subheader("📊 Market Analysis")
        if market_analysis:
            for section in market_analysis.split('\n\n'):
                if section.strip():
                    st.markdown(section)
        else:
            st.info("No market analysis available")

    with tab3:
        st.subheader("💰 Investment Analysis")
        if property_valuations:
            for section in property_valuations.split('\n\n'):
                if section.strip():
                    st.markdown(section)
        else:
            st.info("No valuation data available")