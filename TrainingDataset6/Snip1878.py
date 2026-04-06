def replace_html_links(
    text: list[str],
    links: list[HtmlLinkInfo],
    original_links: list[HtmlLinkInfo],
    lang_code: str,
) -> list[str]:
    """
    Replace HTML links in the given text with the links from the original document.

    Adjust URLs for the given language code.
    Fail if the number of links does not match the original.
    """

    if len(links) != len(original_links):
        raise ValueError(
            "Number of HTML links does not match the number in the "
            "original document "
            f"({len(links)} vs {len(original_links)})"
        )

    modified_text = text.copy()
    for link_index, link in enumerate(links):
        original_link_info = original_links[link_index]

        # Replace in the document text
        replacement_link = _construct_html_link(
            link_text=link["text"],
            attributes=original_link_info["attributes"],
            lang_code=lang_code,
        )
        line_no = link["line_no"] - 1
        modified_text[line_no] = modified_text[line_no].replace(
            link["full_tag"], replacement_link, 1
        )

    return modified_text