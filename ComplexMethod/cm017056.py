def extract_html_links(lines: list[str]) -> list[HtmlLinkInfo]:
    """
    Extract all HTML links from the given lines.

    Return list of HtmlLinkInfo, where each dict contains:
    - `line_no` - line number (1-based)
    - `full_tag` - full HTML link tag
    - `attributes` - list of HTMLLinkAttribute (name, quote, value)
    - `text` - link text
    """

    links = []
    for line_no, line in enumerate(lines, start=1):
        for html_link in HTML_LINK_RE.finditer(line):
            link_str = html_link.group(0)

            link_text_match = HTML_LINK_TEXT_RE.match(link_str)
            assert link_text_match is not None
            link_text = link_text_match.group(2)
            assert isinstance(link_text, str)

            link_open_tag_match = HTML_LINK_OPEN_TAG_RE.match(link_str)
            assert link_open_tag_match is not None
            link_open_tag = link_open_tag_match.group(1)
            assert isinstance(link_open_tag, str)

            attributes: list[HTMLLinkAttribute] = []
            for attr_name, attr_quote, attr_value in re.findall(
                HTML_ATTR_RE, link_open_tag
            ):
                assert isinstance(attr_name, str)
                assert isinstance(attr_quote, str)
                assert isinstance(attr_value, str)
                attributes.append(
                    HTMLLinkAttribute(
                        name=attr_name, quote=attr_quote, value=attr_value
                    )
                )
            links.append(
                HtmlLinkInfo(
                    line_no=line_no,
                    full_tag=link_str,
                    attributes=attributes,
                    text=link_text,
                )
            )
    return links