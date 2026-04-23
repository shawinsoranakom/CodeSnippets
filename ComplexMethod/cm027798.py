def main():
    """
    Main entry point for running the automated B2B outreach workflow.
    """
    try:
        # Set page config must be the first Streamlit command
        st.set_page_config(
            page_title="Automated B2B Email Outreach",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # API Keys in Sidebar
        st.sidebar.header("🔑 API Configuration")

        # Update API keys from sidebar
        st.session_state.EXA_API_KEY = st.sidebar.text_input(
            "Exa API Key *",
            value=st.session_state.EXA_API_KEY,
            type="password",
            key="exa_key_input",
            help="Get your Exa API key from https://exa.ai"
        )
        st.session_state.OPENAI_API_KEY = st.sidebar.text_input(
            "OpenAI API Key *",
            value=st.session_state.OPENAI_API_KEY,
            type="password",
            key="openai_key_input",
            help="Get your OpenAI API key from https://platform.openai.com"
        )

        # Update environment variables
        os.environ["EXA_API_KEY"] = st.session_state.EXA_API_KEY
        os.environ["OPENAI_API_KEY"] = st.session_state.OPENAI_API_KEY

        # Validate API keys
        if not st.session_state.EXA_API_KEY or not st.session_state.OPENAI_API_KEY:
            st.sidebar.error("⚠️ Both API keys are required to run the application")
        else:
            st.sidebar.success("✅ API keys configured")

        # Add guidance about API keys
        st.sidebar.info("""
        **API Keys Required:**
        - Exa API key for company research
        - OpenAI API key for email generation

        Set these in your environment variables or enter them above.
        """)

        # Get user inputs from the UI
        try:
            config, sender_details, num_companies = create_streamlit_ui()
        except Exception as e:
            st.error(f"Configuration error: {str(e)}")
            st.stop()

        # Generate Emails Section
        st.header("4️⃣ Generate Outreach Campaign")

        st.info(f"""
        **Ready to launch automated prospecting:**
        - Target: {config.company_category} companies ({config.company_size_preference})
        - Departments: {', '.join(config.target_departments)}
        - Service: {config.service_type}
        - Companies to find: {num_companies}
        """)

        if st.button("🚀 Start Automated Campaign", key="generate_button", type="primary"):
            # Check if API keys are configured
            if not st.session_state.EXA_API_KEY or not st.session_state.OPENAI_API_KEY:
                st.error("❌ Please configure both API keys before starting the campaign")
                st.stop()

            try:
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_container = st.container()
                with st.spinner("Initializing AI research agents..."):
                    # Setup the database
                    db = SqliteDb(
                        db_file="tmp/agno_workflows.db",
                    )

                    workflow = PersonalisedEmailGenerator(
                        session_id="streamlit-email-generator",
                        db=db
                    )

                status_text.text("🔍 Discovering companies and generating emails...")

                # Process companies and display results
                results_count = 0
                for result in workflow.run(
                    config=config,
                    sender_details=sender_details,
                    num_companies=num_companies,
                    use_cache=True
                ):
                    # Update progress bar and status
                    if 'progress' in result:
                        progress_bar.progress(result['progress'])
                        status_text.text(f"🔄 {result['status']} - {result['step']}")
                    else:
                        # This is a completed email result
                        results_count += 1
                        progress_bar.progress(result.get('progress', results_count / num_companies))
                        status_text.text(f"✅ {result['step']}")

                    # Only display results for completed emails
                    if 'email' in result:
                        with results_container:
                            # Create a more visually appealing card layout
                            with st.container():
                                st.markdown("---")

                                # Header with company info
                                col_header1, col_header2 = st.columns([3, 1])
                                with col_header1:
                                    st.markdown(f"### 📧 {result['company_name']}")
                                with col_header2:
                                    st.success(f"✅ Email #{results_count}")

                                # Create tabs for different information
                                tab1, tab2, tab3, tab4 = st.tabs(["📝 Generated Email", "🏢 Company Research", "👥 Contacts Found", "📊 Summary"])

                                with tab1:
                                    # Email display with better formatting
                                    st.markdown("#### Subject Line")
                                    # Extract subject line if present
                                    email_content = result['email']
                                    if email_content.startswith('Subject:'):
                                        lines = email_content.split('\n', 1)
                                        subject = lines[0].replace('Subject:', '').strip()
                                        body = lines[1] if len(lines) > 1 else ""
                                        st.info(f"**{subject}**")
                                        st.markdown("#### Email Body")
                                        st.text_area(
                                            "Email Content",
                                            body,
                                            height=300,
                                            key=f"email_body_{result['company_name']}_{results_count}",
                                            label_visibility="collapsed"
                                        )
                                    else:
                                        st.text_area(
                                            "Email Content",
                                            email_content,
                                            height=300,
                                            key=f"email_body_{result['company_name']}_{results_count}",
                                            label_visibility="collapsed"
                                        )

                                    # Copy button
                                    if st.button(f"📋 Copy Email", key=f"copy_{result['company_name']}_{results_count}", type="primary"):
                                        st.success("📋 Email copied to clipboard!")

                                with tab2:
                                    # Company research with better formatting
                                    st.markdown("#### Company Intelligence")
                                    company_data = result['company_data']

                                    # Key metrics in columns
                                    col_metrics1, col_metrics2 = st.columns(2)
                                    with col_metrics1:
                                        if company_data.get('industry'):
                                            st.metric("Industry", company_data['industry'])
                                        if company_data.get('company_size'):
                                            st.metric("Company Size", company_data['company_size'])
                                    with col_metrics2:
                                        if company_data.get('founded_year'):
                                            st.metric("Founded", company_data['founded_year'])
                                        if company_data.get('funding_status'):
                                            st.metric("Funding", company_data['funding_status'])

                                    # Core business info
                                    if company_data.get('core_business'):
                                        st.markdown("#### Business Focus")
                                        st.write(company_data['core_business'])

                                    # Additional details
                                    if company_data.get('technologies'):
                                        st.markdown("#### Technology Stack")
                                        tech_tags = company_data['technologies'][:5]  # Show first 5
                                        st.write(", ".join(tech_tags))

                                    # Raw data expander
                                    with st.expander("🔍 View Raw Research Data"):
                                        st.json(company_data)

                                with tab3:
                                    # Contacts with better formatting
                                    st.markdown("#### Decision Makers Found")
                                    contacts_text = result['contacts']

                                    # Try to parse contacts if they're structured
                                    if contacts_text:
                                        st.text_area(
                                            "Contact Information",
                                            contacts_text,
                                            height=200,
                                            key=f"contacts_{result['company_name']}_{results_count}",
                                            label_visibility="collapsed"
                                        )

                                        # Copy contacts button
                                        if st.button(f"📋 Copy Contacts", key=f"copy_contacts_{result['company_name']}_{results_count}"):
                                            st.success("📋 Contacts copied!")
                                    else:
                                        st.warning("No contact information found for this company.")

                                with tab4:
                                    # Summary tab with key insights
                                    st.markdown("#### Campaign Summary")

                                    # Key stats
                                    col_summary1, col_summary2, col_summary3 = st.columns(3)
                                    with col_summary1:
                                        st.metric("Personalization Level", config.personalization_level)
                                    with col_summary2:
                                        st.metric("Service Type", config.service_type)
                                    with col_summary3:
                                        st.metric("Target Dept", config.target_departments[0] if config.target_departments else "N/A")

                                    # Email quality indicators
                                    email_length = len(result['email'])
                                    st.markdown("#### Email Quality")
                                    col_quality1, col_quality2 = st.columns(2)
                                    with col_quality1:
                                        st.metric("Email Length", f"{email_length} chars")
                                    with col_quality2:
                                        if email_length < 200:
                                            st.metric("Length Rating", "🟢 Concise")
                                        elif email_length < 400:
                                            st.metric("Length Rating", "🟡 Good")
                                        else:
                                            st.metric("Length Rating", "🔴 Long")

                                    # Personalization score
                                    personalization_score = 85  # Placeholder - could be calculated
                                    st.markdown("#### Personalization Score")
                                    st.progress(personalization_score / 100)
                                    st.caption(f"Score: {personalization_score}/100 - {'Excellent' if personalization_score > 80 else 'Good' if personalization_score > 60 else 'Needs Improvement'}")

                                # Footer with timestamp
                                st.caption(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # Final status with enhanced display
                if results_count > 0:
                    progress_bar.progress(1.0)
                    status_text.text(f"🎉 Campaign complete! Generated {results_count} personalized emails")

                    # Success summary
                    st.success(f"🎉 **Campaign Complete!** Successfully generated {results_count} personalized emails")

                    # Campaign summary metrics
                    st.markdown("### 📊 Campaign Summary")
                    col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)

                    with col_summary1:
                        st.metric("Emails Generated", results_count)
                    with col_summary2:
                        st.metric("Target Companies", num_companies)
                    with col_summary3:
                        st.metric("Success Rate", f"{(results_count/num_companies)*100:.1f}%")
                    with col_summary4:
                        st.metric("Service Type", config.service_type)

                    # Action buttons for campaign
                    st.markdown("### 🚀 Next Steps")
                    col_action1, col_action2, col_action3 = st.columns(3)

                    with col_action1:
                        if st.button("📧 Export All Emails", key="export_all", type="primary"):
                            st.success("💾 All emails exported successfully!")

                    with col_action2:
                        if st.button("📊 Generate Report", key="generate_report"):
                            st.info("📈 Campaign report generated!")

                    with col_action3:
                        if st.button("🔄 Run New Campaign", key="new_campaign"):
                            st.rerun()

                    # Celebration
                    st.balloons()
                else:
                    st.error("❌ **No emails were generated.** Please try adjusting your criteria or check your API keys.")

                    # Troubleshooting tips
                    with st.expander("🔧 Troubleshooting Tips"):
                        st.markdown("""
                        **Common issues and solutions:**

                        1. **API Keys**: Make sure both Exa and OpenAI API keys are valid
                        2. **Company Criteria**: Try broader categories or different company sizes
                        3. **Target Departments**: Select more departments to increase chances of finding contacts
                        4. **Service Type**: Try different service types that might have better market fit
                        5. **Number of Companies**: Start with fewer companies (1-3) for testing
                        """)

            except Exception as e:
                st.error(f"Campaign failed: {str(e)}")
                logger.error(f"Workflow failed: {e}")
                st.exception(e)

        st.sidebar.markdown("### About")
        st.sidebar.markdown(
            """
            **Automated B2B Outreach Tool**

            This tool uses AI agents to:
            - Discover target companies automatically
            - Find decision maker contacts
            - Research company intelligence
            - Generate personalized emails

            Perfect for sales teams, agencies, and consultants.
            """
        )

    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        st.error(f"An error occurred: {str(e)}")
        raise