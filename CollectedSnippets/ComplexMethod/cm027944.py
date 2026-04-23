def main() -> None:
    st.set_page_config(page_title="GTM B2B Outreach", layout="wide")

    # Sidebar: API keys
    st.sidebar.header("API Configuration")
    openai_key = st.sidebar.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    exa_key = st.sidebar.text_input("Exa API Key", type="password", value=os.getenv("EXA_API_KEY", ""))
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    if exa_key:
        os.environ["EXA_API_KEY"] = exa_key

    if not openai_key or not exa_key:
        st.sidebar.warning("Enter both API keys to enable the app")

    # Inputs
    st.title("GTM B2B Outreach Multi Agent Team")
    st.info(
        "GTM teams often need to reach out for demos and discovery calls, but manual research and personalization is slow. "
        "This app uses GPT-5 with a multi-agent workflow to find target companies, identify contacts, research genuine insights (website + Reddit), "
        "and generate tailored outreach emails in your chosen style."
    )
    col1, col2 = st.columns(2)
    with col1:
        target_desc = st.text_area("Target companies (industry, size, region, tech, etc.)", height=100)
        offering_desc = st.text_area("Your product/service offering (1-3 sentences)", height=100)
    with col2:
        sender_name = st.text_input("Your name", value="Sales Team")
        sender_company = st.text_input("Your company", value="Our Company")
        calendar_link = st.text_input("Calendar link (optional)", value="")
        num_companies = st.number_input("Number of companies", min_value=1, max_value=10, value=5)
        email_style = st.selectbox(
            "Email style",
            options=["Professional", "Casual", "Cold", "Consultative"],
            index=0,
            help="Choose the tone/format for the generated emails",
        )

    if st.button("Start Outreach", type="primary"):
        # Validate
        if not openai_key or not exa_key:
            st.error("Please provide API keys in the sidebar")
        elif not target_desc or not offering_desc:
            st.error("Please fill in target companies and offering")
        else:
            # Stage-by-stage progress UI
            progress = st.progress(0)
            stage_msg = st.empty()
            details = st.empty()
            try:
                # Prepare agents
                company_agent = create_company_finder_agent()
                contact_agent = create_contact_finder_agent()
                research_agent = create_research_agent()
                email_agent = create_email_writer_agent(email_style)

                # 1. Companies
                stage_msg.info("1/4 Finding companies...")
                companies = run_company_finder(
                    company_agent,
                    target_desc.strip(),
                    offering_desc.strip(),
                    max_companies=int(num_companies),
                )
                progress.progress(25)
                details.write(f"Found {len(companies)} companies")

                # 2. Contacts
                stage_msg.info("2/4 Finding contacts (2–3 per company)...")
                contacts_data = run_contact_finder(
                    contact_agent,
                    companies,
                    target_desc.strip(),
                    offering_desc.strip(),
                ) if companies else []
                progress.progress(50)
                details.write(f"Collected contacts for {len(contacts_data)} companies")

                # 3. Research
                stage_msg.info("3/4 Researching insights (website + Reddit)...")
                research_data = run_research(research_agent, companies) if companies else []
                progress.progress(75)
                details.write(f"Compiled research for {len(research_data)} companies")

                # 4. Emails
                stage_msg.info("4/4 Writing personalized emails...")
                emails = run_email_writer(
                    email_agent,
                    contacts_data,
                    research_data,
                    offering_desc.strip(),
                    sender_name.strip() or "Sales Team",
                    sender_company.strip() or "Our Company",
                    calendar_link.strip() or None,
                ) if contacts_data else []
                progress.progress(100)
                details.write(f"Generated {len(emails)} emails")

                st.session_state["gtm_results"] = {
                    "companies": companies,
                    "contacts": contacts_data,
                    "research": research_data,
                    "emails": emails,
                }
                stage_msg.success("Completed")
            except Exception as e:
                stage_msg.error("Pipeline failed")
                st.error(f"{e}")

    # Show results if present
    results = st.session_state.get("gtm_results")
    if results:
        companies = results.get("companies", [])
        contacts = results.get("contacts", [])
        research = results.get("research", [])
        emails = results.get("emails", [])

        st.subheader("Top target companies")
        if companies:
            for idx, c in enumerate(companies, 1):
                st.markdown(f"**{idx}. {c.get('name','')}**  ")
                st.write(c.get("website", ""))
                st.write(c.get("why_fit", ""))
        else:
            st.info("No companies found")
        st.divider()

        st.subheader("Contacts found")
        if contacts:
            for c in contacts:
                st.markdown(f"**{c.get('name','')}**")
                for p in c.get("contacts", [])[:3]:
                    inferred = " (inferred)" if p.get("inferred") else ""
                    st.write(f"- {p.get('full_name','')} | {p.get('title','')} | {p.get('email','')}{inferred}")
        else:
            st.info("No contacts found")
        st.divider()

        st.subheader("Research insights")
        if research:
            for r in research:
                st.markdown(f"**{r.get('name','')}**")
                for insight in r.get("insights", [])[:4]:
                    st.write(f"- {insight}")
        else:
            st.info("No research insights")
        st.divider()

        st.subheader("Suggested Outreach Emails")
        if emails:
            for i, e in enumerate(emails, 1):
                with st.expander(f"{i}. {e.get('company','')} → {e.get('contact','')}"):
                    st.write(f"Subject: {e.get('subject','')}")
                    st.text(e.get("body", ""))
        else:
            st.info("No emails generated")