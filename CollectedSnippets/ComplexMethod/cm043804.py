def _convert_layout_table(table_elem, base_url: str = "") -> str | None:
    """Convert layout tables with multi-line content cells to formatted sections.

    Detects tables where cells contain multiple block elements (like bullet lists
    of checkmark items) and converts them to section headers with bullet lists
    instead of trying to force them into markdown table format.

    Handles three patterns:
    1. Single-column tables with cells containing multiple divs (checkmark lists)
    2. Multi-column tables where one column has headers and another has bullet items (same row)
    3. Tables with alternating header rows and bullet rows
    """
    rows = table_elem.find_all("tr")

    if not rows:
        return None

    # Check if this is a multi-column data table with a header row (not a layout table)
    # Look for a row that has 3+ cells with bold text (indicating a header row)
    for row in rows:
        cells = row.find_all(["td", "th"])
        bold_content_cells = 0
        for cell in cells:
            text = cell.get_text(strip=True)
            if text and text not in ["\xa0", " ", ""]:
                # Check if this cell has bold text
                bold = cell.find(["b", "strong"]) or cell.find(
                    style=re.compile(
                        r"font-weight:\s*(?:bold|bolder|[6-9]00)",
                        re.IGNORECASE,
                    )
                )
                if bold:
                    bold_content_cells += 1
        # If this row has 3+ bold content cells, it's a real data table header
        if bold_content_cells >= 3:
            return None  # Let regular table processing handle this

    # Helper to extract bullet items from a cell with embedded bullets
    def extract_bullet_items(cell):
        """Extract bullet items from a cell containing divs with bullets at start."""
        items = []
        divs = cell.find_all("div", recursive=True)
        for div in divs:
            # Skip empty divs
            div_text = div.get_text(strip=True)
            if not div_text or div_text in ["\xa0", " ", ""]:
                continue
            # Skip divs that are purely containers of other divs
            if div.find("div") and len(div.find_all(string=True, recursive=False)) == 0:
                continue

            # Check if this div starts with a bullet character
            first_char = div_text[0] if div_text else ""
            if first_char in BULLET_CHARS:
                # Convert images in this div
                for img in div.find_all("img"):
                    img.replace_with(_convert_image_to_html(img, base_url))

                text = div.get_text(separator=" ", strip=True)
                text = _clean_html_entities(text)
                text = re.sub(r"\s+", " ", text).strip()
                # Remove leading bullet
                if text and text[0] in BULLET_CHARS:
                    text = text[1:].strip()
                if text:
                    items.append(text)
        return items

    # Helper to extract header text from a cell
    def extract_header_text(cell):
        """Extract header text and anchor ID, handling multi-line name cells.

        Returns tuple of (anchor_id, text) where anchor_id may be None.
        """
        lines = []
        anchor_id = cell.get("id")

        # Also check nested divs for anchor ID
        if not anchor_id:
            for div in cell.find_all("div"):
                div_id = div.get("id")
                if div_id:
                    anchor_id = div_id
                    break

        # First try to get text from bold elements
        for bold in cell.find_all(["b", "strong"]):
            text = bold.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text).strip()
            if text and text not in ["\xa0", " "]:
                lines.append(text)

        # Also check for font-weight:bold in style
        if not lines:
            bold_styled = cell.find(
                style=re.compile(r"font-weight:\s*bold", re.IGNORECASE)
            )
            if bold_styled:
                text = bold_styled.get_text(separator=" ", strip=True)
                text = re.sub(r"\s+", " ", text).strip()
                if text and text not in ["\xa0", " "]:
                    lines.append(text)

        # If no bold elements, try divs
        if not lines:
            for div in cell.find_all("div", recursive=False):
                text = div.get_text(separator=" ", strip=True)
                text = re.sub(r"\s+", " ", text).strip()
                if text and text not in ["\xa0", " "]:
                    lines.append(text)

        text = (
            " ".join(lines)
            if lines
            else cell.get_text(separator=" ", strip=True).strip()
        )
        return (anchor_id, text)

    # Helper to check if a row is a header-only row (bold text, no bullets)
    def is_header_row(row):
        """Check if this row contains only header text (bold, no bullets)."""
        cells = row.find_all(["td", "th"])
        row_text = ""
        has_bold = False
        has_bullets = False

        for cell in cells:
            text = cell.get_text(strip=True)
            if text and text not in ["\xa0", " "]:
                row_text += text
                # Check for bold
                if cell.find(["b", "strong"]) or cell.find(
                    style=re.compile(r"font-weight:\s*bold", re.IGNORECASE)
                ):
                    has_bold = True
                # Check for bullets
                if extract_bullet_items(cell):
                    has_bullets = True

        # It's a header row if it has bold text, no bullets, and reasonable length
        return has_bold and not has_bullets and row_text and len(row_text) < 150

    # ===== PATTERN 0: Bio-style tables with rowspan paragraph cells =====
    # Detect tables that have cells with rowspan containing paragraph content
    # (e.g., director biographies in proxy statements)
    bio_sections = []
    for row in rows:
        cells = row.find_all(["td", "th"])
        for cell in cells:
            rowspan = int(cell.get("rowspan", 1) or 1)
            if rowspan > 1:
                # This cell spans multiple rows - check if it has paragraph content
                cell_text = cell.get_text(strip=True)
                # Bio cells typically have 200+ characters of paragraph text
                if len(cell_text) > 200:
                    # Found a potential bio cell - extract header from same or nearby rows
                    # Look for a bold name cell in an earlier row of this table
                    name_text = None

                    # Search backward through rows for header
                    row_idx = rows.index(row)
                    for prev_idx in range(row_idx - 1, -1, -1):
                        prev_row = rows[prev_idx]
                        prev_cells = prev_row.find_all(["td", "th"])
                        for prev_cell in prev_cells:
                            prev_text = prev_cell.get_text(strip=True)
                            if not prev_text or prev_text in ["\xa0", " "]:
                                continue
                            # Check for bold name
                            bold = prev_cell.find(["b", "strong"]) or prev_cell.find(
                                style=re.compile(r"font-weight:\s*bold", re.IGNORECASE)
                            )
                            # A name is typically short, bold, and all caps or title case
                            if bold and len(prev_text) < 50 and prev_text.isupper():
                                name_text = prev_text
                                break
                        if name_text:
                            break

                    # Also extract metadata from the same row (title, tenure, age, etc.)
                    metadata_items = []
                    seen_metadata = set()
                    for other_cell in cells:
                        if other_cell == cell:
                            continue
                        other_text = other_cell.get_text(strip=True)
                        if not other_text or other_text in ["\xa0", " "]:
                            continue
                        # Skip if too long (probably another bio)
                        if len(other_text) > 150:
                            continue
                        # Extract items from divs (direct children only)
                        for div in other_cell.find_all("div", recursive=False):
                            div_text = div.get_text(strip=True)
                            div_text = _clean_html_entities(div_text)
                            div_text = re.sub(r"\s+", " ", div_text).strip()
                            if (
                                div_text
                                and div_text not in ["\xa0", " ", ""]
                                and div_text not in seen_metadata
                            ):
                                metadata_items.append(div_text)
                                seen_metadata.add(div_text)

                    # Extract bio paragraphs from the cell
                    # Only get top-level divs to avoid duplicates from nested divs
                    bio_paragraphs = []
                    seen_texts = set()
                    for div in cell.find_all("div", recursive=False):
                        div_text = div.get_text(strip=True)
                        div_text = _clean_html_entities(div_text)
                        div_text = re.sub(r"\s+", " ", div_text).strip()
                        if (
                            div_text
                            and div_text not in ["\xa0", " ", ""]
                            and len(div_text) > 20
                            and div_text not in seen_texts
                        ):
                            bio_paragraphs.append(div_text)
                            seen_texts.add(div_text)

                    if bio_paragraphs:
                        bio_sections.append(
                            {
                                "name": name_text,
                                "metadata": metadata_items,
                                "paragraphs": bio_paragraphs,
                            }
                        )

    # If we found bio sections, format them
    if bio_sections:
        result_parts = []
        for section in bio_sections:
            if section["name"]:
                result_parts.append(f"\n**{section['name']}**\n")
            for item in section.get("metadata", []):  # type: ignore
                result_parts.append(f"- {item}")
            if section["metadata"]:
                result_parts.append("")  # Blank line after metadata
            for para in section.get("paragraphs", []):  # type: ignore
                result_parts.append(para)
                result_parts.append("")  # Blank line after each paragraph
        if result_parts:
            return "\n".join(result_parts)

    # ===== PATTERN 2: Multi-column table with headers and bullet content in SAME row =====
    # Check if this is a table with header column + bullet column
    result_sections = []

    for row in rows:
        cells = row.find_all(["td", "th"])
        if not cells:
            continue

        # Find cells with content
        header_cell = None
        bullet_cell = None

        for cell in cells:
            cell_text = cell.get_text(strip=True)
            if not cell_text or cell_text in ["\xa0", " "]:
                continue

            # Check if this cell contains bullet items
            bullet_items = extract_bullet_items(cell)
            if bullet_items:
                bullet_cell = (cell, bullet_items)
            else:
                # Check if this looks like a header cell (bold, short text)
                bold = cell.find(["b", "strong"]) or cell.find(
                    style=re.compile(r"font-weight:\s*bold", re.IGNORECASE)
                )
                if bold and len(cell_text) < 200:
                    header_cell = cell

        if bullet_cell:
            header_anchor = None
            header_text = ""
            if header_cell:
                header_anchor, header_text = extract_header_text(header_cell)

            result_sections.append((header_anchor, header_text, bullet_cell[1]))

    # If we found header+bullet sections (same row), format them
    # Only use this pattern if we found headers for at least some rows
    if result_sections:
        has_headers = any(h for _, h, _ in result_sections)
        if has_headers:
            result_parts = []
            for header_anchor, header_text, bullet_items in result_sections:
                if header_text:
                    if header_anchor:
                        result_parts.append(
                            f'\n<a id="{header_anchor}"></a>**{header_text}**\n'
                        )
                    else:
                        result_parts.append(f"\n**{header_text}**\n")
                for item in bullet_items:
                    result_parts.append(f"- {item}")
                result_parts.append("")

            if result_parts:
                return "\n".join(result_parts)

    # ===== PATTERN 3: Alternating header rows and bullet rows =====
    # Process rows in sequence, building sections
    sections = []
    current_header = ""
    current_anchor = None
    current_bullets = []

    for row in rows:
        cells = row.find_all(["td", "th"])
        if not cells:
            continue

        row_text = "".join(c.get_text(strip=True) for c in cells)
        if not row_text or row_text in ["\xa0", " "]:
            continue

        # Collect all bullet items from this row
        row_bullets = []
        for cell in cells:
            row_bullets.extend(extract_bullet_items(cell))

        if row_bullets:
            # This is a bullet row
            current_bullets.extend(row_bullets)
        elif is_header_row(row):
            # This is a header row
            # Save previous section if exists
            if current_bullets:
                sections.append((current_anchor, current_header, current_bullets))
                current_bullets = []

            # Get header text and anchor from this row
            header_parts = []
            current_anchor = None
            for cell in cells:
                anchor_id, text = extract_header_text(cell)
                if anchor_id and not current_anchor:
                    current_anchor = anchor_id
                if text and text not in ["\xa0", " "]:
                    header_parts.append(text)
            current_header = " ".join(header_parts)

    # Don't forget the last section
    if current_bullets:
        sections.append((current_anchor, current_header, current_bullets))

    # If we found alternating sections, format them
    if sections and len(sections) >= 1:
        # Verify this looks like a structured document (not just random bullets)
        total_bullets = sum(len(s[2]) for s in sections)
        if total_bullets >= 3:
            result_parts = []
            for header_anchor, header_text, bullet_items in sections:
                if header_text:
                    if header_anchor:
                        result_parts.append(
                            f'\n<a id="{header_anchor}"></a>**{header_text}**\n'
                        )
                    else:
                        result_parts.append(f"\n**{header_text}**\n")
                for item in bullet_items:
                    result_parts.append(f"- {item}")
                result_parts.append("")

            if result_parts:
                return "\n".join(result_parts)

    # ===== PATTERN 1: Single column with multi-div cells (checkmark lists) =====
    # First, find the header row (if any) and content rows
    header_cells: list = []
    content_cells: list = []

    for row in rows:
        cells = row.find_all(["td", "th"])

        # Check if this row looks like a header row
        is_header = False
        if row.find("th"):
            is_header = True
        else:
            # Check if cells have bold text and minimal content (header-like)
            for cell in cells:
                text = cell.get_text(strip=True)
                if text and len(text) < 80:
                    bold = cell.find(["b", "strong"]) or cell.find(
                        style=re.compile(r"font-weight:\s*bold", re.IGNORECASE)
                    )
                    if bold:
                        is_header = True
                        break

        if is_header and not header_cells:
            for cell in cells:
                text = cell.get_text(strip=True)
                if text and text not in ["\xa0", " "]:
                    header_cells.append(text)
        else:
            # This is a content row - check for multi-line cells
            for cell in cells:
                # Count meaningful divs in this cell
                content_divs = []
                for div in cell.find_all("div", recursive=False):
                    div_text = div.get_text(strip=True)
                    if div_text and div_text not in ["\xa0", " ", ""]:
                        content_divs.append(div)

                if len(content_divs) >= 3:
                    # This cell has multiple items - extract them
                    items = []
                    for div in content_divs:
                        # Convert images in this div
                        for img in div.find_all("img"):
                            img.replace_with(_convert_image_to_html(img, base_url))

                        text = div.get_text(separator=" ", strip=True)
                        text = _clean_html_entities(text)
                        text = re.sub(r"\s+", " ", text).strip()
                        if text:
                            items.append(text)

                    if items:
                        content_cells.append(items)

    # If we didn't find any multi-line content cells, this isn't a layout table
    if not content_cells:
        return None

    # Build the output: pair headers with their content lists
    result_parts = []

    for i, items in enumerate(content_cells):
        if i < len(header_cells):
            # Add header
            result_parts.append(f"\n**{header_cells[i]}**\n")

        # Add items as bullet list
        for item in items:
            result_parts.append(f"- {item}")
        result_parts.append("")  # Blank line after each section

    if result_parts:
        return "\n".join(result_parts)

    return None