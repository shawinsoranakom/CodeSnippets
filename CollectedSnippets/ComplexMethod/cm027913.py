def generate_comparison_report(competitor_data: list) -> None:
            # Create DataFrame directly from competitor data
            if not competitor_data:
                st.error("No competitor data available for comparison")
                return

            # Prepare data for DataFrame
            table_data = []
            for competitor in competitor_data:
                row = {
                    'Company': f"{competitor.get('company_name', 'N/A')} ({competitor.get('competitor_url', 'N/A')})",
                    'Pricing': competitor.get('pricing', 'N/A')[:100] + '...' if len(competitor.get('pricing', '')) > 100 else competitor.get('pricing', 'N/A'),
                    'Key Features': ', '.join(competitor.get('key_features', [])[:3]) if competitor.get('key_features') else 'N/A',
                    'Tech Stack': ', '.join(competitor.get('tech_stack', [])[:3]) if competitor.get('tech_stack') else 'N/A',
                    'Marketing Focus': competitor.get('marketing_focus', 'N/A')[:100] + '...' if len(competitor.get('marketing_focus', '')) > 100 else competitor.get('marketing_focus', 'N/A'),
                    'Customer Feedback': competitor.get('customer_feedback', 'N/A')[:100] + '...' if len(competitor.get('customer_feedback', '')) > 100 else competitor.get('customer_feedback', 'N/A')
                }
                table_data.append(row)

            # Create DataFrame
            df = pd.DataFrame(table_data)

            # Display the table
            st.subheader("Competitor Comparison")
            st.dataframe(df, use_container_width=True)

            # Also show raw data for debugging
            with st.expander("View Raw Competitor Data"):
                st.json(competitor_data)