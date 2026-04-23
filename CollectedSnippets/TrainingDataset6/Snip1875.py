def replace_markdown_links(
    text: list[str],
    links: list[MarkdownLinkInfo],
    original_links: list[MarkdownLinkInfo],
    lang_code: str,
) -> list[str]:
    """
    Replace markdown links in the given text with the original links.

    Fail if the number of links does not match the original.
    """

    if len(links) != len(original_links):
        raise ValueError(
            "Number of markdown links does not match the number in the "
            "original document "
            f"({len(links)} vs {len(original_links)})"
        )

    modified_text = text.copy()
    for i, link_info in enumerate(links):
        link_text = link_info["text"]
        link_title = link_info["title"]
        original_link_info = original_links[i]

        # Replace
        replacement_link = _construct_markdown_link(
            url=original_link_info["url"],
            text=link_text,
            title=link_title,
            attributes=original_link_info["attributes"],
            lang_code=lang_code,
        )
        line_no = link_info["line_no"] - 1
        modified_line = modified_text[line_no]
        modified_line = modified_line.replace(
            link_info["full_match"], replacement_link, 1
        )
        modified_text[line_no] = modified_line

    return modified_text