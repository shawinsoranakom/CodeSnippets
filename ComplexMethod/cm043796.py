def get_text_content(
    element, preserve_links_in_text: bool = False, base_url: str = ""
) -> str:
    """Get text from element, handling XBRL wrappers and preserving word boundaries.

    If preserve_links_in_text is True, converts <a> tags to markdown [text](href) format.
    """
    if isinstance(element, NavigableString):
        return str(element)

    texts = []
    for child in element.children:
        if isinstance(child, NavigableString):
            texts.append(str(child))
        elif child.name == "br":
            texts.append(" ")  # Treat line breaks as spaces
        elif child.name == "a" and preserve_links_in_text:
            # Convert link to markdown format
            href = child.get("href", "")
            link_text = child.get_text(strip=True)
            if href and link_text:
                # Keep anchor links as-is, resolve relative links
                if (
                    not href.startswith("#")
                    and base_url
                    and not href.startswith(("http://", "https://"))
                ):
                    href = urljoin(base_url, href)
                texts.append(f"[{link_text}]({href})")
            else:
                texts.append(link_text or "")
        elif child.name and child.name.startswith("ix:"):
            # XBRL wrapper - get its text content
            texts.append(child.get_text(separator=" "))
        else:
            texts.append(get_text_content(child, preserve_links_in_text, base_url))

    result_parts: list = []
    had_whitespace_separator = False

    for _t in texts:
        t = _t.replace("\xa0", " ")  # Normalize non-breaking spaces first

        if not t.strip():
            # This prevents split words like <b>INCOM</b><b>E</b> → "INCOM E"
            # while preserving spaces where <b>WORD1</b><b> </b><b>WORD2</b>.
            if result_parts:
                had_whitespace_separator = True
            continue

        if result_parts:
            last_char = result_parts[-1][-1] if result_parts[-1] else ""
            first_char = t[0] if t else ""

            if had_whitespace_separator:
                # Explicit whitespace between parts — add space unless
                # punctuation rules say not to
                if (
                    last_char not in NO_SPACE_AFTER
                    and first_char not in NO_SPACE_BEFORE
                ):
                    result_parts.append(" ")
                # Adjacent elements of the same type with no separator
                # (e.g. <b>INCOM</b><b>E</b>) are parts of one word.
            elif not (last_char.isalpha() and first_char.isalpha()) and (
                last_char not in NO_SPACE_AFTER and first_char not in NO_SPACE_BEFORE
            ):
                result_parts.append(" ")

            had_whitespace_separator = False

        result_parts.append(t)

    result = "".join(result_parts)
    # Collapse any remaining multiple spaces
    result = re.sub(r" +", " ", result)
    return result