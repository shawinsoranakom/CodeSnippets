def rich_text_to_markdown(rich_text_array: List[dict]) -> str:
    """
    Convert Notion rich text array to markdown with formatting.

    Args:
        rich_text_array: Array of rich text objects from Notion.

    Returns:
        Markdown formatted string.
    """
    if not rich_text_array:
        return ""

    markdown_parts = []

    for text_obj in rich_text_array:
        text = text_obj.get("plain_text", "")
        annotations = text_obj.get("annotations", {})

        # Apply formatting based on annotations
        if annotations.get("code"):
            text = f"`{text}`"
        else:
            if annotations.get("bold"):
                text = f"**{text}**"
            if annotations.get("italic"):
                text = f"*{text}*"
            if annotations.get("strikethrough"):
                text = f"~~{text}~~"
            if annotations.get("underline"):
                text = f"<u>{text}</u>"

        # Handle links
        if text_obj.get("href"):
            text = f"[{text}]({text_obj['href']})"

        markdown_parts.append(text)

    return "".join(markdown_parts)