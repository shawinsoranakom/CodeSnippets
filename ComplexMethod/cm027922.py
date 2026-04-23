def main():
    st.set_page_config(
        page_title="Local AI Real Estate Agent Team", 
        page_icon="🏠", 
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Clean header
    st.title("🏠 Local AI Real Estate Agent Team")
    st.caption("Find Your Dream Home with Local Ollama AI Agents")

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # API Key inputs with validation
        with st.expander("🔑 API Keys", expanded=True):
            firecrawl_key = st.text_input(
                "Firecrawl API Key", 
                value=DEFAULT_FIRECRAWL_API_KEY, 
                type="password",
                help="Get your API key from https://firecrawl.dev",
                placeholder="fc_..."
            )

            # Update environment variables
            if firecrawl_key: os.environ["FIRECRAWL_API_KEY"] = firecrawl_key

            # Ollama model info
            st.info("🤖 Using Ollama model: gpt-oss:20b (local)")
            st.markdown("Make sure Ollama is running with: `ollama run gpt-oss:20b`")

        # Website selection
        with st.expander("🌐 Search Sources", expanded=True):
            st.markdown("**Select real estate websites to search:**")
            available_websites = ["Zillow", "Realtor.com", "Trulia", "Homes.com"]
            selected_websites = [site for site in available_websites if st.checkbox(site, value=site in ["Zillow", "Realtor.com"])]

            if selected_websites:
                st.markdown(f'✅ {len(selected_websites)} sources selected')
            else:
                st.markdown('⚠️ Please select at least one website')

        # How it works
        with st.expander("🤖 How It Works", expanded=False):
            st.markdown("**🔍 Property Search Agent**")
            st.markdown("Uses direct Firecrawl integration to find properties")

            st.markdown("**📊 Market Analysis Agent**")
            st.markdown("Analyzes market trends and neighborhood insights")

            st.markdown("**💰 Property Valuation Agent**")
            st.markdown("Evaluates properties and provides investment analysis")

    # Main form
    st.header("Your Property Requirements")
    st.info("Please provide the location, budget, and property details to help us find your ideal home.")

    with st.form("property_preferences"):
        # Location and Budget Section
        st.markdown("### 📍 Location & Budget")
        col1, col2 = st.columns(2)

        with col1:
            city = st.text_input(
                "🏙️ City", 
                placeholder="e.g., San Francisco",
                help="Enter the city where you want to buy property"
            )
            state = st.text_input(
                "🗺️ State/Province (optional)", 
                placeholder="e.g., CA",
                help="Enter the state or province (optional)"
            )

        with col2:
            min_price = st.number_input(
                "💰 Minimum Price ($)", 
                min_value=0, 
                value=500000, 
                step=50000,
                help="Your minimum budget for the property"
            )
            max_price = st.number_input(
                "💰 Maximum Price ($)", 
                min_value=0, 
                value=1500000, 
                step=50000,
                help="Your maximum budget for the property"
            )

        # Property Details Section
        st.markdown("### 🏡 Property Details")
        col1, col2, col3 = st.columns(3)

        with col1:
            property_type = st.selectbox(
                "🏠 Property Type",
                ["Any", "House", "Condo", "Townhouse", "Apartment"],
                help="Type of property you're looking for"
            )
            bedrooms = st.selectbox(
                "🛏️ Bedrooms",
                ["Any", "1", "2", "3", "4", "5+"],
                help="Number of bedrooms required"
            )

        with col2:
            bathrooms = st.selectbox(
                "🚿 Bathrooms",
                ["Any", "1", "1.5", "2", "2.5", "3", "3.5", "4+"],
                help="Number of bathrooms required"
            )
            min_sqft = st.number_input(
                "📏 Minimum Square Feet",
                min_value=0,
                value=1000,
                step=100,
                help="Minimum square footage required"
            )

        with col3:
            timeline = st.selectbox(
                "⏰ Timeline",
                ["Flexible", "1-3 months", "3-6 months", "6+ months"],
                help="When do you plan to buy?"
            )
            urgency = st.selectbox(
                "🚨 Urgency",
                ["Not urgent", "Somewhat urgent", "Very urgent"],
                help="How urgent is your purchase?"
            )

        # Special Features
        st.markdown("### ✨ Special Features")
        special_features = st.text_area(
            "🎯 Special Features & Requirements",
            placeholder="e.g., Parking, Yard, View, Near public transport, Good schools, Walkable neighborhood, etc.",
            help="Any specific features or requirements you're looking for"
        )

        # Submit button with custom styling
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "🚀 Start Property Analysis",
                type="primary",
                use_container_width=True
            )

    # Process form submission
    if submitted:
        # Validate all required inputs
        missing_items = []
        if not firecrawl_key:
            missing_items.append("Firecrawl API Key")
        if not city:
            missing_items.append("City")
        if not selected_websites:
            missing_items.append("At least one website selection")

        if missing_items:
            st.error(f"⚠️ Please provide: {', '.join(missing_items)}")
            return

        try:
            user_criteria = {
                'budget_range': f"${min_price:,} - ${max_price:,}",
                'property_type': property_type,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'min_sqft': min_sqft,
                'special_features': special_features if special_features else 'None specified'
            }

        except Exception as e:
            st.error(f"❌ Error initializing: {str(e)}")
            return

        # Display progress
        st.markdown("#### Property Analysis in Progress")
        st.info("AI Agents are searching for your perfect home...")

        status_container = st.container()
        with status_container:
            st.markdown("### 📊 Current Activity")
            progress_bar = st.progress(0)
            current_activity = st.empty()

        def update_progress(progress, status, activity=None):
            if activity:
                progress_bar.progress(progress)
                current_activity.text(activity)

        try:
            start_time = time.time()
            update_progress(0.1, "Initializing...", "Starting sequential property analysis")

            # Run sequential analysis with manual coordination
            final_result = run_sequential_analysis(
                city=city,
                state=state,
                user_criteria=user_criteria,
                selected_websites=selected_websites,
                firecrawl_api_key=firecrawl_key,
                update_callback=update_progress
            )

            total_time = time.time() - start_time

            # Display results
            if isinstance(final_result, dict):
                # Use the new professional display
                display_properties_professionally(
                    final_result['properties'],
                    final_result['market_analysis'],
                    final_result['property_valuations'],
                    final_result['total_properties']
                )

            st.markdown("### 🏠 Comprehensive Real Estate Analysis")
            st.markdown(final_result)

            # Download button with better styling
            download_content = final_result['markdown_synthesis'] if isinstance(final_result, dict) else final_result

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="📄 Download Full Report",
                    data=download_content,
                    file_name="property_analysis_report.md",
                    mime="text/markdown",
                    use_container_width=True
                )

            # Timing info in a subtle way
            st.caption(f"Analysis completed in {total_time:.1f}s")

        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")