def _extract_header_text(table_elem) -> str | None:
    """Extract single-cell header table as markdown header, preserving anchors."""
    rows = table_elem.find_all("tr")
    for row in rows:
        cells = row.find_all(["td", "th"])
        for cell in cells:
            text = cell.get_text(strip=True)
            if text:
                text = _clean_html_entities(text)
                text = re.sub(r"\s+", " ", text).strip()

                # Look for anchor id on the cell or nested divs
                anchor_id = cell.get("id")
                if not anchor_id:
                    # Check nested divs for id attribute
                    for div in cell.find_all("div"):
                        div_id = div.get("id")
                        if div_id:
                            anchor_id = div_id
                            break

                # Return as bold header with anchor if present
                if anchor_id:
                    return f'\n<a id="{anchor_id}"></a>**{text}**\n'
                return f"\n**{text}**\n"
    return None