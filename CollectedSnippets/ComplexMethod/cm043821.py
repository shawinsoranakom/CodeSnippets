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