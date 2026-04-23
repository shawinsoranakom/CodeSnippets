def _extract_cell_text(
    cell, base_url: str = "", preserve_line_breaks: bool = False
) -> str:
    """Extract text from a table cell, preserving links and images as markdown.

    If preserve_line_breaks is True, detects cells with multiple block elements
    (like divs with checkmark images) and preserves them as separate lines.

    Always preserves <br> tags within cells as HTML line breaks.
    """
    # Check if this cell contains ONLY a footnote reference (sup tag with a number)
    # These appear in SEC tables as separate cells and should be merged with the label
    sup_tags = cell.find_all("sup")
    if sup_tags:
        # Get all text content excluding sup tags and invisible content
        non_sup_text = ""
        for elem in cell.descendants:
            if isinstance(elem, NavigableString):
                parent = elem.parent
                # Skip text inside sup tags
                is_in_sup = False
                while parent:
                    if parent.name == "sup":
                        is_in_sup = True
                        break
                    parent = parent.parent
                if not is_in_sup:
                    # Not inside a sup tag - check if it's visible text
                    text = str(elem).strip()
                    # Skip hidden/invisible content (zero-width spaces, nbsp, etc)
                    if text and text not in ["\u200b", "\xa0", " ", ""]:
                        non_sup_text += text

        non_sup_text = non_sup_text.strip()
        if not non_sup_text:
            # Cell only has sup content - check if it's a footnote reference (small number)
            sup_text = " ".join(sup.get_text(strip=True) for sup in sup_tags)
            # Footnote references are typically 1-3 digit numbers
            if re.match(r"^\s*\d{1,3}\s*$", sup_text):
                # Return as superscript HTML - will be merged with previous cell later
                return f"<sup>{sup_text.strip()}</sup>"

    # Work on a copy so we don't mutate the original
    cell_copy = copy(cell)

    # Convert BR tags to a space so they don't leak as literal "<br>" into markdown.
    # In preserve_line_breaks mode keep a newline marker instead.
    for br in cell_copy.find_all("br"):
        br.replace_with(" " if not preserve_line_breaks else "\n")

    # Check if this cell has multiple block-level divs with content (like bullet lists)
    # This detects layout cells that should NOT be flattened
    content_divs = []
    for div in cell_copy.find_all("div", recursive=False):
        div_text = div.get_text(strip=True)
        # Skip empty divs and spacer divs (just nbsp)
        if div_text and div_text not in ["\xa0", " ", ""]:
            content_divs.append(div)

    # If cell has 3+ content divs, treat as multi-line content
    if preserve_line_breaks and len(content_divs) >= 3:
        lines = []
        for div in content_divs:
            # Convert images in this div
            for img in div.find_all("img"):
                img.replace_with(_convert_image_to_html(img, base_url))
            # Convert links in this div
            for a in div.find_all("a"):
                href = a.get("href", "")
                link_text = a.get_text(strip=True)
                if href and link_text:
                    if base_url and not href.startswith(("#", "http://", "https://")):
                        href = urljoin(base_url, href)
                    a.replace_with(f"[{link_text}]({href})")
                elif link_text:
                    a.replace_with(link_text)

            text = div.get_text(separator=" ", strip=True)
            text = _clean_html_entities(text)
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                lines.append(text)

        if lines:
            # Return with special marker for multi-line cells
            return "\n".join(lines)

    # Standard single-line extraction
    # Convert links to markdown format
    for a in cell_copy.find_all("a"):
        href = a.get("href", "")
        link_text = a.get_text(strip=True)
        if href and link_text:
            if base_url and not href.startswith(("#", "http://", "https://")):
                href = urljoin(base_url, href)
            a.replace_with(f"[{link_text}]({href})")
        elif link_text:
            a.replace_with(link_text)

    # Strip images from table cells — SEC filings use <img> for decorative
    # elements (brackets, braces, spacers) that have no textual meaning.
    # Use the alt attribute only if it carries actual content (not the generic
    # "Image" placeholder that BeautifulSoup/browsers supply by default).
    for img in cell_copy.find_all("img"):
        alt = img.get("alt", "").strip()
        img.replace_with(alt if alt and alt.lower() not in ("image", "img", "") else "")

    # Get text with space separator
    text = cell_copy.get_text(separator=" ", strip=True)
    text = _clean_html_entities(text)
    text = re.sub(r"\s+", " ", text).strip()
    # Common word-fragment suffixes that indicate a broken word, not a compound
    _WORD_SUFFIXES = r"MENTS|MENT|TIONS|ATED|TING|NESS|ABLE|IBLE"
    # Rejoin words broken by line wrapping in narrow HTML columns
    # Pattern 1: "ADJUST- MENTS" → "ADJUSTMENTS" (soft hyphen, no <br>)
    text = re.sub(r"(\w)- (?!<br>)(\w)", r"\1\2", text)
    # Pattern 2a: "ADJUST- <br> MENTS" → "ADJUSTMENTS" (word-break hyphen + br)
    # When the continuation is a word fragment (suffix), remove the hyphen
    text = re.sub(rf"(\w)- (?:<br> ?)+({_WORD_SUFFIXES})\b", r"\1\2", text)
    # Pattern 2b: "PERCENTAGE- <br> POINT" → "PERCENTAGE-POINT" (compound + br)
    # When the continuation is a full word, keep the hyphen
    text = re.sub(r"(\w)- (?:<br> ?)+(\w)", r"\1-\2", text)
    # Pattern 3: "ADJUST MENTS" → "ADJUSTMENTS" (space from word-wrap in source)
    text = re.sub(
        rf"\b([A-Z]{{2,}}) ({_WORD_SUFFIXES})\b",
        r"\1\2",
        text,
    )
    # Normalize <br> spacing: " <br> " → "<br>"
    text = re.sub(r"\s*<br>\s*", "<br>", text)
    return text