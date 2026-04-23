def _extract_bullet_list(table_elem) -> str | None:
    """Extract bullet list from table format.

    Note: * is NOT included as it's typically a footnote marker, not a bullet.

    Special handling: If the content cell has a bold header at the beginning,
    format as a subsection header (#### Header) followed by the description.
    """
    bullets = []
    rows = table_elem.find_all("tr")

    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 2:
            bullet_col = -1
            for idx, cell in enumerate(cells[:2]):
                if cell.get_text(strip=True) in BULLET_CHARS:
                    bullet_col = idx
                    break

            if bullet_col >= 0:
                content_cell = (
                    cells[bullet_col + 1] if bullet_col + 1 < len(cells) else None
                )
                if content_cell:
                    # Check if this cell starts with bold text (subsection header pattern)
                    bold_elem = content_cell.find(["b", "strong"])
                    if not bold_elem:
                        # Check for font-weight:bold in nested divs
                        bold_elem = content_cell.find(
                            style=re.compile(r"font-weight:\s*bold", re.IGNORECASE)
                        )

                    if bold_elem:
                        # Use separator=" " to preserve spacing between inline elements
                        bold_text = bold_elem.get_text(separator=" ").strip()
                        bold_text = re.sub(
                            r"\s+", " ", bold_text
                        )  # Normalize whitespace
                        full_text = content_cell.get_text(separator=" ", strip=True)
                        full_text = _clean_html_entities(full_text)
                        full_text = re.sub(r"\s+", " ", full_text).strip()

                        # If bold text is at the start and there's more content after
                        if (
                            full_text.startswith(bold_text)
                            and len(full_text) > len(bold_text) + 5
                        ):
                            # This is a subsection header: "**Header**. Description..."
                            rest = full_text[len(bold_text) :].strip()
                            if rest.startswith("."):
                                rest = rest[1:].strip()
                            bullets.append(f"**{bold_text}**. {rest}")
                        else:
                            # Just bold text with no description
                            bullets.append(f"**{bold_text}**")
                    else:
                        # Regular bullet item
                        text = " ".join(
                            c.get_text(separator=" ", strip=True)
                            for c in cells[bullet_col + 1 :]
                        )
                        text = _clean_html_entities(text)
                        text = re.sub(r"\s+", " ", text).strip()
                        if text and len(text) > 3:
                            bullets.append(f"- {text}")
        elif len(cells) == 1:
            text = cells[0].get_text(separator=" ", strip=True)
            text = _clean_html_entities(text)
            text = re.sub(r"\s+", " ", text).strip()
            if text and text[0] in BULLET_CHARS:
                text = text[1:].strip()
                if text:
                    bullets.append(f"- {text}")

    return "\n\n".join(bullets) if bullets else None