def create_streamlit_ui():
    """Create the Streamlit user interface"""
    st.title("🚀 Automated B2B Email Outreach Generator")
    st.markdown("""
    **Fully automated prospecting pipeline**: Discovers companies, finds decision makers, 
    and generates personalized emails using AI research agents.
    """)

    # Step 1: Target Company Category Selection
    st.header("1️⃣ Target Company Discovery")

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_category = st.selectbox(
            "What type of companies should we target?",
            options=list(COMPANY_CATEGORIES.keys()),
            key="company_category"
        )

        st.info(f"📌 {COMPANY_CATEGORIES[selected_category]['description']}")

        st.markdown("### Typical Decision Makers We'll Find:")
        for role in COMPANY_CATEGORIES[selected_category]['typical_roles']:
            st.markdown(f"- {role}")

    with col2:
        st.markdown("### Company Size Filter")
        company_size = st.radio(
            "Preferred company size",
            ["All Sizes", "Startup (1-50)", "SMB (51-500)", "Enterprise (500+)"],
            key="company_size"
        )

        num_companies = st.number_input(
            "Number of companies to find",
            min_value=1,
            max_value=20,
            value=5,
            help="AI will discover this many companies automatically"
        )

    # Step 2: Your Information
    st.header("2️⃣ Your Contact Information")

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Required Information")
        sender_details = {
            "name": st.text_input("Your Name *", key="sender_name"),
            "email": st.text_input("Your Email *", key="sender_email"),
            "organization": st.text_input("Your Organization *", key="sender_org")
        }

    with col4:
        st.subheader("Optional Information")
        sender_details.update({
            "linkedin": st.text_input("LinkedIn Profile (optional)", key="sender_linkedin", placeholder="https://linkedin.com/in/yourname"),
            "phone": st.text_input("Phone Number (optional)", key="sender_phone", placeholder="+1 (555) 123-4567"),
            "website": st.text_input("Company Website (optional)", key="sender_website", placeholder="https://yourcompany.com"),
            "calendar_link": st.text_input("Calendar Link (optional)", key="sender_calendar", placeholder="https://calendly.com/yourname")
        })

    # Service description
    sender_details["service_offered"] = st.text_area(
        "Describe your offering *",
        height=100,
        key="service_description",
        help="Explain what you offer and how it helps businesses",
        placeholder="We help companies build custom AI solutions that automate workflows and improve efficiency..."
    )

    # Step 3: Service Type and Targeting
    st.header("3️⃣ Outreach Configuration")

    col5, col6 = st.columns(2)

    with col5:
        service_type = st.selectbox(
            "Service/Product Category",
            [
                "Software Solution",
                "Consulting Services", 
                "Professional Services",
                "Technology Platform",
                "Custom Development"
            ],
            key="service_type"
        )

    with col6:
        personalization_level = st.select_slider(
            "Email Personalization Level",
            options=["Basic", "Medium", "Deep"],
            value="Deep",
            help="Deep personalization takes longer but produces better results"
        )

    # Step 4: Target Department Selection
    target_departments = st.multiselect(
        "Which departments should we target?",
        [
            "GTM (Sales & Marketing)",
            "Human Resources", 
            "Engineering/Tech",
            "Operations",
            "Finance",
            "Product",
            "Executive Leadership"
        ],
        default=["GTM (Sales & Marketing)"],
        key="target_departments",
        help="AI will find decision makers in these departments"
    )

    # Validate required inputs
    required_fields = ["name", "email", "organization", "service_offered"]
    missing_fields = [field for field in required_fields if not sender_details.get(field)]

    if missing_fields:
        st.error(f"Please fill in required fields: {', '.join(missing_fields)}")
        st.stop()

    if not target_departments:
        st.error("Please select at least one target department")
        st.stop()

    if not selected_category:
        st.error("Please select a company category")
        st.stop()

    if not service_type:
        st.error("Please select a service type")
        st.stop()

    # Create and return configuration
    outreach_config = OutreachConfig(
        company_category=selected_category,
        target_departments=target_departments,
        service_type=service_type,
        company_size_preference=company_size,
        personalization_level=personalization_level
    )

    return outreach_config, sender_details, num_companies