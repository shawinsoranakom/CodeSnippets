def strip_markdown_links(text: str) -> str:
    """Replace markdown links with just their visible text."""
    return md_link_pattern.sub(r"\1", text)