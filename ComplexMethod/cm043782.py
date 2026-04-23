def is_header_element(tag) -> bool:
    """Check if element looks like a section header."""
    if tag.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        return True

    # Elements explicitly marked as body text by the reflow engine
    # should never be promoted to headings.
    if tag.get("data-body-text"):
        return False

    # Check for TOC section headers - elements with toc* anchor IDs
    element_id = tag.get("id", "")

    if element_id and element_id.startswith("toc"):
        # Check if it contains bold/styled text indicating a section header
        bold_child = tag.find(["b", "strong"]) or tag.find(
            style=re.compile(r"font-weight:\s*bold", re.IGNORECASE)
        )
        if bold_child:
            text = tag.get_text().strip()

            if text and len(text) < 150:
                return True

    # Check for divs/paragraphs styled as headers (large font-size)
    if tag.name in ["div", "p"]:
        # Positioned layouts (Workiva) nest tables inside styled divs
        # whose font-size or bold spans would otherwise false-positive.
        if tag.find("table"):
            return False

        style = tag.get("style", "")
        # Look for font-size in style attribute
        font_match = re.search(r"font-size:\s*(\d+)(?:pt|px)", style)

        if font_match:
            font_size = int(font_match.group(1))
            # Check if child spans have a SMALLER font size — if so, the
            # container font-size is just a fallback/default (common in
            # position-based layouts) and should NOT trigger header detection.
            child_font = None

            for span in tag.find_all("span", recursive=True):
                s = span.get("style", "")
                cm = re.search(r"font-size:\s*(\d+)(?:pt|px)", s)

                if cm:
                    child_font = int(cm.group(1))
                    break

            effective_font = child_font if child_font is not None else font_size
            # 11pt+ is typically header-sized in SEC filings
            if effective_font >= 11:
                text = tag.get_text().strip()
                # Should be reasonably short and have content
                if text and len(text) < 150:
                    return True

        # Only trigger when the div has no bare text nodes — positioned divs always wrap text in spans.
        has_bare_text = any(
            isinstance(c, NavigableString) and c.strip() for c in tag.children
        )
        if not has_bare_text:
            # Check for <p>/<div> whose only children are <b>/<strong> tags
            non_ws_children = [
                c
                for c in tag.children
                if not (isinstance(c, NavigableString) and not c.strip())
            ]
            all_bold_tags = (
                non_ws_children
                and all(
                    (hasattr(c, "name") and c.name in ("b", "strong"))
                    or (
                        hasattr(c, "name")
                        and c.name == "span"
                        and not c.get_text(strip=True)
                    )
                    for c in non_ws_children
                )
                # At least one child must be <b>/<strong>
                and any(
                    hasattr(c, "name") and c.name in ("b", "strong")
                    for c in non_ws_children
                )
            )
            if all_bold_tags and not tag.find("img"):
                text = tag.get_text().strip()
                if text and len(text) < 100 and re.search(r"[a-zA-Z]", text):
                    return True

            text_spans = [
                s
                for s in tag.find_all("span", recursive=True)
                if any(isinstance(c, NavigableString) and c.strip() for c in s.children)
                and "display:inline-block" not in s.get("style", "").replace(" ", "")
            ]
            if text_spans:
                # Count bold vs total characters across text spans.
                bold_chars = 0
                total_chars = 0

                for s in text_spans:
                    sty = s.get("style", "")
                    is_b = bool(
                        re.search(
                            r"font-weight:\s*(bold|bolder|[6-9]00)",
                            sty,
                            re.I,
                        )
                    )
                    for c in s.children:
                        if isinstance(c, NavigableString) and c.strip():
                            n = len(c.strip())
                            total_chars += n
                            if is_b:
                                bold_chars += n

                mostly_bold = total_chars > 0 and bold_chars / total_chars >= 0.8

                if mostly_bold:
                    text = tag.get_text().strip()

                    if text and len(text) < 80 and re.search(r"[a-zA-Z]", text):
                        return True

    if tag.name in ["b", "strong"]:
        text = tag.get_text().strip()

        if re.match(r"^ITEM\s+\d", text, re.IGNORECASE):
            return True

        if re.match(r"^PART\s+[IVX]+", text, re.IGNORECASE):
            return True

        words = text.split()

        if len(words) >= 2 and len(text) < 80 and text.isupper():
            return True
        # Single uppercase words that look like section titles
        if len(words) == 1 and text.isupper() and len(text) >= 4:
            return True

    return False