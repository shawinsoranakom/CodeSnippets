def run(
        self,
        config: OutreachConfig,
        sender_details: Dict[str, str],
        num_companies: int = 5,
        use_cache: bool = True,
    ):
        """
        Automated B2B outreach workflow:

        1. Discover companies using Exa search based on criteria
        2. Find decision maker contacts for each company
        3. Research company details for personalization
        4. Generate personalized emails
        """
        logger.info("Starting automated B2B outreach workflow...")

        # Step 1: Discover companies
        logger.info("🔍 Discovering target companies...")
        search_query = f"""
        Find {num_companies} {config.company_category} companies that would be good prospects for {config.service_type}.

        Company criteria:
        - Industry: {config.company_category}
        - Size: {config.company_size_preference}
        - Target departments: {', '.join(config.target_departments)}

        Look for companies showing growth, recent funding, or expansion.
        """

        companies_response = self.company_finder.run(search_query)
        if not companies_response or not companies_response.content:
            logger.error("No companies found")
            return

        # Parse companies from response
        companies_text = companies_response.content
        logger.info(f"Found companies: {companies_text[:200]}...")

        # Step 2: For each company, find contacts and research
        for i in range(num_companies):
            try:
                logger.info(f"Processing company #{i+1}")

                # Yield progress update
                yield {
                    "step": f"Processing company {i+1}/{num_companies}",
                    "progress": (i + 0.2) / num_companies,
                    "status": "Finding contacts..."
                }

                # Extract company info from the response
                company_search = f"Extract company #{i+1} details from: {companies_text}"

                # Step 3: Find decision maker contacts
                logger.info("👥 Finding decision maker contacts...")
                contacts_query = f"""
                Find decision makers at company #{i+1} from this list: {companies_text}

                Focus on roles in: {', '.join(config.target_departments)}
                Find their email addresses and LinkedIn profiles.
                """

                contacts_response = self.contact_finder.run(contacts_query)
                if not contacts_response or not contacts_response.content:
                    logger.warning(f"No contacts found for company #{i+1}")
                    continue

                # Yield progress update
                yield {
                    "step": f"Processing company {i+1}/{num_companies}",
                    "progress": (i + 0.4) / num_companies,
                    "status": "Researching company..."
                }

                # Step 4: Research company details
                logger.info("🔬 Researching company details...")
                research_query = f"""
                Research company #{i+1} from this list: {companies_text}

                Focus on insights relevant for {config.service_type} outreach.
                Find pain points related to {', '.join(config.target_departments)}.
                """

                research_response = self.company_researcher.run(research_query)
                if not research_response or not research_response.content:
                    logger.warning(f"No research data for company #{i+1}")
                    continue

                # Parse the research response content
                research_content = research_response.content
                if not research_content:
                    logger.warning(f"No research data for company #{i+1}")
                    continue

                # Create a basic company info structure from the research
                company_data = CompanyInfo(
                    company_name=f"Company #{i+1}",  # Will be updated with actual name
                    website_url="",  # Will be updated with actual URL
                    industry="Unknown",
                    core_business=research_content[:200] if research_content else "No data available"
                )

                # Yield progress update
                yield {
                    "step": f"Processing company {i+1}/{num_companies}",
                    "progress": (i + 0.6) / num_companies,
                    "status": "Generating email..."
                }

                # Step 5: Generate personalized email
                logger.info("✉️ Generating personalized email...")

                # Get appropriate template based on target departments
                template_dept = config.target_departments[0] if config.target_departments else "GTM (Sales & Marketing)"
                if template_dept in DEPARTMENT_TEMPLATES and config.service_type in DEPARTMENT_TEMPLATES[template_dept]:
                    template = DEPARTMENT_TEMPLATES[template_dept][config.service_type]
                else:
                    template = DEPARTMENT_TEMPLATES["GTM (Sales & Marketing)"]["Software Solution"]

                email_context = json.dumps(
                    {
                        "template": template,
                        "company_info": company_data.model_dump(),
                        "contacts_info": contacts_response.content,
                        "sender_details": sender_details,
                        "target_departments": config.target_departments,
                        "service_type": config.service_type,
                        "personalization_level": config.personalization_level
                    },
                    indent=4,
                )

                email_response = self.email_creator.run(
                    f"Generate a personalized email using this context:\n{email_context}"
                )

                if not email_response or not email_response.content:
                    logger.warning(f"No email generated for company #{i+1}")
                    continue

                yield {
                    "company_name": company_data.company_name,
                    "email": email_response.content,
                    "company_data": company_data.model_dump(),
                    "contacts": contacts_response.content,
                    "step": f"Company {i+1}/{num_companies} completed",
                    "progress": (i + 1) / num_companies,
                    "status": "Completed"
                }

            except Exception as e:
                logger.error(f"Error processing company #{i+1}: {e}")
                continue