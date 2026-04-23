def format_unit_suffix(unit: str | None, scale: str | None) -> str:
    """Format unit and scale into a display suffix.

    Parameters
    ----------
    unit : str | None
        The unit of measurement (e.g., "US Dollar", "Percent").
    scale : str | None
        The scale/multiplier (e.g., "Millions", "Billions").

    Returns
    -------
    str
        A formatted suffix like "(Percent)" or "(US Dollar, Millions)",
        or empty string if no meaningful unit/scale provided.
    """
    parts = []
    # Ensure unit and scale are valid strings (not None, nan, or other types)
    if unit and isinstance(unit, str) and unit not in ("-", "nan", ""):
        parts.append(unit)
    if scale and isinstance(scale, str) and scale not in ("Units", "-", "nan", ""):
        parts.append(scale)
    if parts:
        return f" ({', '.join(parts)})"
    return ""