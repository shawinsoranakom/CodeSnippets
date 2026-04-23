def parse_unit_and_scale(unit_string: str | None) -> tuple[str | None, str | None]:
    """Parse a combined unit string into separate scale and unit components.

    Many IMF indicator labels embed both scale and unit in a single suffix like:
    - "Per capita, US dollar" → scale="Per capita", unit="US dollar"
    - "Millions, US dollar" → scale="Millions", unit="US dollar"
    - "US Dollar, Millions" → scale="Millions", unit="US Dollar"
    - "US dollars per metric tonne" → unit="US dollars", scale="per metric tonne"
    - "US cents per pound" → unit="US cents", scale="per pound"
    - "Percent" → scale=None, unit="Percent"
    - "US dollar" → scale=None, unit="US dollar"
    - "Index" → scale=None, unit="Index"

    Parameters
    ----------
    unit_string : str | None
        The combined unit/scale string extracted from a label.

    Returns
    -------
    tuple[str | None, str | None]
        A tuple of (unit, scale) where:
        - unit: The unit of measurement (e.g., "US dollar", "Percent")
        - scale: The scale/multiplier (e.g., "Per capita", "Millions", "per metric tonne")
    """
    if not unit_string:
        return None, None

    # Check for "Unit of ..." pattern (e.g., "Percent of exports of goods and services")
    # Common units that can be followed by "of ..."
    unit_of_patterns = ["Percent of ", "Ratio of ", "Index of ", "Number of "]
    for pattern in unit_of_patterns:
        if unit_string.startswith(pattern):
            unit = pattern.replace(" of ", "").strip()
            scale = "of " + unit_string[len(pattern) :].strip().title()
            return unit, scale

    # Check for "X per Y" pattern (e.g., "US dollars per metric tonne")
    # Split on " per " - unit is before, scale is "per ..."
    if " per " in unit_string.lower():
        # Find the position case-insensitively
        lower_str = unit_string.lower()
        per_idx = lower_str.find(" per ")
        if per_idx > 0:
            unit = unit_string[:per_idx].strip()
            scale = unit_string[per_idx + 1 :].strip().title()
            return unit, scale

    # Scale indicators that appear before the unit (e.g., "Per capita, US dollar")
    scale_prefixes = [
        "Per capita, ",
        "Percent, ",
        "Millions, ",
        "Billions, ",
        "Thousands, ",
        "Mean, ",
    ]

    for prefix in scale_prefixes:
        if unit_string.startswith(prefix):
            scale = prefix.rstrip(", ")
            unit = unit_string[len(prefix) :]
            return unit, scale

    # Scale indicators that appear after the unit (e.g., "US Dollar, Millions")
    scale_suffixes = [
        ", Millions",
        ", Billions",
        ", Thousands",
        ", Per capita",
    ]

    for suffix in scale_suffixes:
        if unit_string.endswith(suffix):
            scale = suffix.lstrip(", ")
            unit = unit_string[: -len(suffix)]
            return unit, scale

    # Check for pattern: "scale_description, Unit" (e.g., "95 percent interval - lower bound, Percent")
    # The unit is after the last comma, scale is before it
    unit_keywords = [
        "Percent",
        "US dollar",
        "US Dollar",
        "Index",
        "Ratio",
        "SDR",
        "EUR",
        "Domestic currency",
        "National currency",
        "Euro",
    ]
    last_comma = unit_string.rfind(", ")
    if last_comma > 0:
        potential_unit = unit_string[last_comma + 2 :]
        if potential_unit in unit_keywords:
            scale = unit_string[:last_comma]
            return potential_unit, scale

    # If no scale prefix/suffix, the whole string is the unit
    # But check if it's actually a scale-only value
    scale_only_values = ["Per capita", "Millions", "Billions", "Thousands"]
    if unit_string in scale_only_values:
        return None, unit_string

    return unit_string, None