def _is_code_paragraph(para) -> bool:
    """Return True if all text-bearing runs in the paragraph use a monospace font."""
    runs_with_text = [r for r in para.runs if r.text.strip()]
    if not runs_with_text:
        return False
    runs_with_font = [r for r in runs_with_text if r.font.name]
    # At least one run must have an explicit font, and all such runs must be monospace
    if not runs_with_font:
        return False
    return all(r.font.name in _CODE_FONTS for r in runs_with_font)