def _detect_heading_level(para, body_font_size: float) -> int:
    """Return heading level (0 = not a heading, 1-6 = heading level)."""
    # Prefer Word built-in Heading styles
    style_name = para.style.name if para.style else ""
    if style_name.startswith("Heading"):
        try:
            return int(style_name.split()[-1])
        except ValueError:
            return 1
    if style_name == "Title":
        return 1
    if style_name == "Subtitle":
        return 2

    text = para.text.strip()
    if not text:
        return 0

    # Use font size of the first run that has an explicit size
    font_size = None
    for run in para.runs:
        if run.font.size:
            font_size = run.font.size.pt
            break

    # Significantly larger than body font -> treat as heading (threshold: 1.5x, short paragraphs only)
    if font_size and font_size > body_font_size * 1.5:
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            return 1
        if len(text) <= 60:
            return 2

    # Chinese numbered heading patterns
    if _RE_H2.match(text):
        return 2
    if _RE_H3.match(text):
        return 3

    return 0