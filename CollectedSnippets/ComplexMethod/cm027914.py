def run_sequential_analysis(city, state, user_criteria, selected_websites, firecrawl_api_key, google_api_key, update_callback):
    """Run agents sequentially with manual coordination"""

    # Initialize agents
    llm = Gemini(id="gemini-2.5-flash", api_key=google_api_key)
    property_search_agent, market_analysis_agent, property_valuation_agent = create_sequential_agents(llm, user_criteria)

    # Step 1: Property Search with Direct Firecrawl Integration
    update_callback(0.2, "Searching properties...", "🔍 Property Search Agent: Finding properties...")

    direct_agent = DirectFirecrawlAgent(
        firecrawl_api_key=firecrawl_api_key,
        google_api_key=google_api_key,
        model_id="gemini-2.5-flash"
    )

    properties_data = direct_agent.find_properties_direct(
        city=city,
        state=state,
        user_criteria=user_criteria,
        selected_websites=selected_websites
    )

    if "error" in properties_data:
        return f"Error in property search: {properties_data['error']}"

    properties = properties_data.get('properties', [])
    if not properties:
        return "No properties found matching your criteria."

    update_callback(0.4, "Properties found", f"✅ Found {len(properties)} properties")

    # Step 2: Market Analysis
    update_callback(0.5, "Analyzing market...", "📊 Market Analysis Agent: Analyzing market trends...")

    market_analysis_prompt = f"""
    Provide CONCISE market analysis for these properties:

    PROPERTIES: {len(properties)} properties in {city}, {state}
    BUDGET: {user_criteria.get('budget_range', 'Any')}

    Give BRIEF insights on:
    • Market condition (buyer's/seller's market)
    • Key neighborhoods where properties are located
    • Investment outlook (2-3 bullet points max)

    Keep each section under 100 words. Use bullet points.
    """

    market_result: RunOutput = market_analysis_agent.run(market_analysis_prompt)
    market_analysis = market_result.content

    update_callback(0.7, "Market analysis complete", "✅ Market analysis completed")

    # Step 3: Property Valuation
    update_callback(0.8, "Evaluating properties...", "💰 Property Valuation Agent: Evaluating properties...")

    # Create detailed property list for valuation
    properties_for_valuation = []
    for i, prop in enumerate(properties, 1):
        if isinstance(prop, dict):
            prop_data = {
                'number': i,
                'address': prop.get('address', 'Address not available'),
                'price': prop.get('price', 'Price not available'),
                'property_type': prop.get('property_type', 'Type not available'),
                'bedrooms': prop.get('bedrooms', 'Not specified'),
                'bathrooms': prop.get('bathrooms', 'Not specified'),
                'square_feet': prop.get('square_feet', 'Not specified')
            }
        else:
            prop_data = {
                'number': i,
                'address': getattr(prop, 'address', 'Address not available'),
                'price': getattr(prop, 'price', 'Price not available'),
                'property_type': getattr(prop, 'property_type', 'Type not available'),
                'bedrooms': getattr(prop, 'bedrooms', 'Not specified'),
                'bathrooms': getattr(prop, 'bathrooms', 'Not specified'),
                'square_feet': getattr(prop, 'square_feet', 'Not specified')
            }
        properties_for_valuation.append(prop_data)

    valuation_prompt = f"""
    Provide CONCISE property assessments for each property. Use the EXACT format shown below:

    USER BUDGET: {user_criteria.get('budget_range', 'Any')}

    PROPERTIES TO EVALUATE:
    {json.dumps(properties_for_valuation, indent=2)}

    For EACH property, provide assessment in this EXACT format:

    **Property [NUMBER]: [ADDRESS]**
    • Value: [Fair price/Over priced/Under priced] - [brief reason]
    • Investment Potential: [High/Medium/Low] - [brief reason]
    • Recommendation: [One actionable insight]

    REQUIREMENTS:
    - Start each assessment with "**Property [NUMBER]:**"
    - Keep each property assessment under 50 words
    - Analyze ALL {len(properties)} properties individually
    - Use bullet points as shown
    """

    valuation_result: RunOutput = property_valuation_agent.run(valuation_prompt)
    property_valuations = valuation_result.content

    update_callback(0.9, "Valuation complete", "✅ Property valuations completed")

    # Step 4: Final Synthesis
    update_callback(0.95, "Synthesizing results...", "🤖 Synthesizing final recommendations...")

    # Debug: Check properties structure
    print(f"Properties type: {type(properties)}")
    print(f"Properties length: {len(properties)}")
    if properties:
        print(f"First property type: {type(properties[0])}")
        print(f"First property: {properties[0]}")

    # Format properties for better display
    properties_display = ""
    for i, prop in enumerate(properties, 1):
        # Handle both dict and object access
        if isinstance(prop, dict):
            address = prop.get('address', 'Address not available')
            price = prop.get('price', 'Price not available')
            prop_type = prop.get('property_type', 'Type not available')
            bedrooms = prop.get('bedrooms', 'Not specified')
            bathrooms = prop.get('bathrooms', 'Not specified')
            square_feet = prop.get('square_feet', 'Not specified')
            agent_contact = prop.get('agent_contact', 'Contact not available')
            description = prop.get('description', 'No description available')
            listing_url = prop.get('listing_url', '#')
        else:
            # Handle object access
            address = getattr(prop, 'address', 'Address not available')
            price = getattr(prop, 'price', 'Price not available')
            prop_type = getattr(prop, 'property_type', 'Type not available')
            bedrooms = getattr(prop, 'bedrooms', 'Not specified')
            bathrooms = getattr(prop, 'bathrooms', 'Not specified')
            square_feet = getattr(prop, 'square_feet', 'Not specified')
            agent_contact = getattr(prop, 'agent_contact', 'Contact not available')
            description = getattr(prop, 'description', 'No description available')
            listing_url = getattr(prop, 'listing_url', '#')

        properties_display += f"""
### Property {i}: {address}

**Price:** {price}  
**Type:** {prop_type}  
**Bedrooms:** {bedrooms} | **Bathrooms:** {bathrooms}  
**Square Feet:** {square_feet}  
**Agent Contact:** {agent_contact}  

**Description:** {description}  

**Listing URL:** [View Property]({listing_url})  

---
"""

    final_synthesis = f"""
# 🏠 Property Listings Found

**Total Properties:** {len(properties)} properties matching your criteria

{properties_display}

---

# 📊 Market Analysis & Investment Insights

        {market_analysis}

---

# 💰 Property Valuations & Recommendations

        {property_valuations}

---

# 🔗 All Property Links
    """

    # Extract and add property links
    all_text = f"{json.dumps(properties, indent=2)} {market_analysis} {property_valuations}"
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', all_text)

    if urls:
        final_synthesis += "\n### Available Property Links:\n"
        for i, url in enumerate(set(urls), 1):
            final_synthesis += f"{i}. {url}\n"

    update_callback(1.0, "Analysis complete", "🎉 Complete analysis ready!")

    # Return structured data for better UI display
    return {
        'properties': properties,
        'market_analysis': market_analysis,
        'property_valuations': property_valuations,
        'markdown_synthesis': final_synthesis,
        'total_properties': len(properties)
    }