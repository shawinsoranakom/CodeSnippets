def extract_unit_scale_from_title(title: str) -> tuple[str | None, str | None]:
    """Extract unit/scale from a trailing parenthetical suffix or comma-separated part.

    Handles two patterns:
    1. Parenthetical: "Title (US Dollar, Millions)" -> unit="US Dollar", scale="Millions"
    2. Comma-separated: "Lamb, Unit prices, US cents per pound" -> unit="US cents per pound"

    Only returns values when the suffix contains known unit/scale keywords to
    avoid over-eager parsing for titles that merely contain contextual labels.
    """
    if not title:
        return None, None

    unit_val: str | None = None
    scale_val: str | None = None

    # First try parenthetical pattern: "Title (unit, scale)"
    if title.endswith(")"):
        paren_start = title.rfind(" (")
        if paren_start > 0:
            suffix_content = title[paren_start + 2 : -1]
            if any(pattern in suffix_content for pattern in UNIT_SCALE_PATTERNS):
                parts = [p.strip() for p in suffix_content.split(",") if p.strip()]

                if len(parts) == 1:
                    only = parts[0]
                    if only in UNIT_SCALE_PATTERNS:
                        scale_val = only
                    else:
                        unit_val = only
                elif len(parts) >= 2:
                    unit_val = parts[0]
                    scale_val = parts[1]

                return unit_val, scale_val

    # Try comma-separated pattern: "Title, Unit prices, US cents per pound"
    # Look for the last comma-separated part that contains unit keywords
    parts = [p.strip() for p in title.split(",")]
    if len(parts) >= 2:
        # Check last part for unit keywords
        last_part = parts[-1].lower()
        if any(kw in last_part for kw in UNIT_KEYWORDS):
            unit_val = parts[-1].strip()
            return unit_val, scale_val

    return None, None