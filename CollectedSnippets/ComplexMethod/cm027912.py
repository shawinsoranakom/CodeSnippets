def extract_competitor_info(competitor_url: str) -> Optional[dict]:
            try:
                # Initialize FirecrawlApp with API key
                app = FirecrawlApp(api_key=st.session_state.firecrawl_api_key)

                # Add wildcard to crawl subpages
                url_pattern = f"{competitor_url}/*"

                extraction_prompt = """
                Extract detailed information about the company's offerings, including:
                - Company name and basic information
                - Pricing details, plans, and tiers
                - Key features and main capabilities
                - Technology stack and technical details
                - Marketing focus and target audience
                - Customer feedback and testimonials

                Analyze the entire website content to provide comprehensive information for each field.
                """

                response = app.extract(
                    [url_pattern],
                    prompt=extraction_prompt,
                    schema=CompetitorDataSchema.model_json_schema()
                )

                # Handle ExtractResponse object
                try:
                    if hasattr(response, 'success') and response.success:
                        if hasattr(response, 'data') and response.data:
                            extracted_info = response.data

                            # Create JSON structure
                            competitor_json = {
                                "competitor_url": competitor_url,
                                "company_name": extracted_info.get('company_name', 'N/A') if isinstance(extracted_info, dict) else getattr(extracted_info, 'company_name', 'N/A'),
                                "pricing": extracted_info.get('pricing', 'N/A') if isinstance(extracted_info, dict) else getattr(extracted_info, 'pricing', 'N/A'),
                                "key_features": extracted_info.get('key_features', [])[:5] if isinstance(extracted_info, dict) and extracted_info.get('key_features') else getattr(extracted_info, 'key_features', [])[:5] if hasattr(extracted_info, 'key_features') else ['N/A'],
                                "tech_stack": extracted_info.get('tech_stack', [])[:5] if isinstance(extracted_info, dict) and extracted_info.get('tech_stack') else getattr(extracted_info, 'tech_stack', [])[:5] if hasattr(extracted_info, 'tech_stack') else ['N/A'],
                                "marketing_focus": extracted_info.get('marketing_focus', 'N/A') if isinstance(extracted_info, dict) else getattr(extracted_info, 'marketing_focus', 'N/A'),
                                "customer_feedback": extracted_info.get('customer_feedback', 'N/A') if isinstance(extracted_info, dict) else getattr(extracted_info, 'customer_feedback', 'N/A')
                            }

                            return competitor_json
                        else:
                            return None
                    else:
                        return None

                except Exception as response_error:
                    return None

            except Exception as e:
                return None