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