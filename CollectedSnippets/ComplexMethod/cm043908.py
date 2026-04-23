def extract_unit_from_label(label: str) -> str | None:
    """Extract unit information from an indicator label.

    Parses indicator labels to extract unit suffixes like:
    - "Per capita, US dollar" from "Exporter real gross domestic product, Per capita, US dollar"
    - "Percent" from "GDP growth rate, Percent"
    - "US Dollar, Millions" from "Trade balance (US Dollar, Millions)"

    Parameters
    ----------
    label : str
        The indicator label to parse.

    Returns
    -------
    str | None
        The extracted unit string, or None if no unit found.
    """
    if not label:
        return None

    # Check for parenthetical unit at end: "(US Dollar, Millions)" or "(Domestic currency)"
    if label.endswith(")"):
        paren_start = label.rfind(" (")
        if paren_start > 0:
            suffix_content = label[paren_start + 2 : -1]
            # Check if it looks like a unit (contains currency or scale keywords)
            unit_keywords = [
                "dollar",
                "Dollar",
                "USD",
                "Euro",
                "euro",
                "Yen",
                "yen",
                "Percent",
                "percent",
                "%",
                "Millions",
                "Billions",
                "Thousands",
                "Units",
                "Per capita",
                "per capita",
                "Index",
                "index",
                "Domestic currency",
                "National currency",
                "currency",
                "SDR",
            ]
            if any(kw in suffix_content for kw in unit_keywords):
                return suffix_content

    # Check for comma-separated unit suffix at the end of the label
    # Look for the last comma-separated part and check if it's a unit
    parts = label.rsplit(", ", 1)
    if len(parts) == 2:
        last_part = parts[1]
        last_part_lower = last_part.lower()
        # "per" indicates a rate/unit (e.g., "US cents per pound", "dollars per metric tonne")
        if " per " in last_part_lower:
            return last_part
        # Check for other unit keywords
        unit_keywords_lower = [
            "dollar",
            "percent",
            "index",
            "ratio",
            "currency",
            "capita",
            "cent",
        ]
        if any(kw in last_part_lower for kw in unit_keywords_lower):
            return last_part

    return None