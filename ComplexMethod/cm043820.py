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