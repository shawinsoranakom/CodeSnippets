def extract_location(location):
    """Extract full location info as dict from location tuple or None."""
    if location is None:
        return {"lineno": 0, "end_lineno": 0, "column": 0, "end_column": 0}
    if isinstance(location, tuple) and len(location) >= 4:
        return {
            "lineno": location[0] if location[0] is not None else 0,
            "end_lineno": location[1] if location[1] is not None else 0,
            "column": location[2] if location[2] is not None else 0,
            "end_column": location[3] if location[3] is not None else 0,
        }
    # Fallback for old-style location
    lineno = location[0] if isinstance(location, tuple) else location
    return {"lineno": lineno or 0, "end_lineno": lineno or 0, "column": 0, "end_column": 0}