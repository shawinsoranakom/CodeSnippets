def extract_property_valuation(property_valuations, property_number, property_address):
    """Extract valuation for a specific property from the full analysis"""
    if not property_valuations:
        return None

    # Split by property sections - look for the formatted property headers
    sections = property_valuations.split('**Property')

    # Look for the specific property number
    for section in sections:
        if section.strip().startswith(f"{property_number}:"):
            # Add back the "**Property" prefix and clean up
            clean_section = f"**Property{section}".strip()
            # Remove any extra asterisks at the end
            clean_section = clean_section.replace('**', '**').replace('***', '**')
            return clean_section

    # Fallback: look for property number mentions in any format
    all_sections = property_valuations.split('\n\n')
    for section in all_sections:
        if (f"Property {property_number}" in section or 
            f"#{property_number}" in section):
            return section

    # Last resort: try to match by address
    for section in all_sections:
        if any(word in section.lower() for word in property_address.lower().split()[:3] if len(word) > 2):
            return section

    # If no specific match found, return indication that analysis is not available
    return f"**Property {property_number} Analysis**\n• Analysis: Individual assessment not available\n• Recommendation: Review general market analysis in the Market Analysis tab"