def get_header_level(tag) -> int:
    """Determine header level."""
    text = tag.get_text().strip()
    if re.match(r"^PART\s+[IVX]+", text, re.IGNORECASE):
        return 1
    if re.match(r"^ITEM\s+\d", text, re.IGNORECASE):
        return 2
    if tag.name == "h1":
        return 1
    if tag.name == "h2":
        return 2
    if tag.name == "h3":
        return 3

    # Check font-size for styled divs/paragraphs
    if tag.name in ["div", "p"]:
        style = tag.get("style", "")
        font_match = re.search(r"font-size:\s*(\d+)(?:pt|px)", style)
        if font_match:
            font_size = int(font_match.group(1))
            if font_size >= 15:
                return 2  # Large headers (15-16pt)
            if font_size >= 11:
                return 3  # Subsection headers (11-14pt)
    return 3