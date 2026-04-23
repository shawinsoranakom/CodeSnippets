def block_to_markdown(block: dict, indent_level: int = 0) -> str:
    """
    Convert a single Notion block to markdown.

    Args:
        block: Block object from Notion API.
        indent_level: Current indentation level for nested blocks.

    Returns:
        Markdown string representation of the block.
    """
    block_type = block.get("type")
    indent = "  " * indent_level
    markdown_lines = []

    # Handle different block types
    if block_type == "paragraph":
        text = rich_text_to_markdown(block["paragraph"].get("rich_text", []))
        if text:
            markdown_lines.append(f"{indent}{text}")

    elif block_type == "heading_1":
        text = parse_rich_text(block["heading_1"].get("rich_text", []))
        markdown_lines.append(f"{indent}# {text}")

    elif block_type == "heading_2":
        text = parse_rich_text(block["heading_2"].get("rich_text", []))
        markdown_lines.append(f"{indent}## {text}")

    elif block_type == "heading_3":
        text = parse_rich_text(block["heading_3"].get("rich_text", []))
        markdown_lines.append(f"{indent}### {text}")

    elif block_type == "bulleted_list_item":
        text = rich_text_to_markdown(block["bulleted_list_item"].get("rich_text", []))
        markdown_lines.append(f"{indent}- {text}")

    elif block_type == "numbered_list_item":
        text = rich_text_to_markdown(block["numbered_list_item"].get("rich_text", []))
        # Note: This is simplified - proper numbering would need context
        markdown_lines.append(f"{indent}1. {text}")

    elif block_type == "to_do":
        text = rich_text_to_markdown(block["to_do"].get("rich_text", []))
        checked = "x" if block["to_do"].get("checked") else " "
        markdown_lines.append(f"{indent}- [{checked}] {text}")

    elif block_type == "toggle":
        text = rich_text_to_markdown(block["toggle"].get("rich_text", []))
        markdown_lines.append(f"{indent}<details>")
        markdown_lines.append(f"{indent}<summary>{text}</summary>")
        markdown_lines.append(f"{indent}")
        # Process children if they exist
        if block.get("children"):
            for child in block["children"]:
                child_markdown = block_to_markdown(child, indent_level + 1)
                if child_markdown:
                    markdown_lines.append(child_markdown)
        markdown_lines.append(f"{indent}</details>")

    elif block_type == "code":
        code = parse_rich_text(block["code"].get("rich_text", []))
        language = block["code"].get("language", "")
        markdown_lines.append(f"{indent}```{language}")
        markdown_lines.append(f"{indent}{code}")
        markdown_lines.append(f"{indent}```")

    elif block_type == "quote":
        text = rich_text_to_markdown(block["quote"].get("rich_text", []))
        markdown_lines.append(f"{indent}> {text}")

    elif block_type == "divider":
        markdown_lines.append(f"{indent}---")

    elif block_type == "image":
        image = block["image"]
        url = image.get("external", {}).get("url") or image.get("file", {}).get(
            "url", ""
        )
        caption = parse_rich_text(image.get("caption", []))
        alt_text = caption if caption else "Image"
        markdown_lines.append(f"{indent}![{alt_text}]({url})")
        if caption:
            markdown_lines.append(f"{indent}*{caption}*")

    elif block_type == "video":
        video = block["video"]
        url = video.get("external", {}).get("url") or video.get("file", {}).get(
            "url", ""
        )
        caption = parse_rich_text(video.get("caption", []))
        markdown_lines.append(f"{indent}[Video]({url})")
        if caption:
            markdown_lines.append(f"{indent}*{caption}*")

    elif block_type == "file":
        file = block["file"]
        url = file.get("external", {}).get("url") or file.get("file", {}).get("url", "")
        caption = parse_rich_text(file.get("caption", []))
        name = caption if caption else "File"
        markdown_lines.append(f"{indent}[{name}]({url})")

    elif block_type == "bookmark":
        url = block["bookmark"].get("url", "")
        caption = parse_rich_text(block["bookmark"].get("caption", []))
        markdown_lines.append(f"{indent}[{caption if caption else url}]({url})")

    elif block_type == "equation":
        expression = block["equation"].get("expression", "")
        markdown_lines.append(f"{indent}$${expression}$$")

    elif block_type == "callout":
        text = rich_text_to_markdown(block["callout"].get("rich_text", []))
        icon = block["callout"].get("icon", {})
        if icon.get("emoji"):
            markdown_lines.append(f"{indent}> {icon['emoji']} {text}")
        else:
            markdown_lines.append(f"{indent}> ℹ️ {text}")

    elif block_type == "child_page":
        title = block["child_page"].get("title", "Untitled")
        markdown_lines.append(f"{indent}📄 [{title}](notion://page/{block['id']})")

    elif block_type == "child_database":
        title = block["child_database"].get("title", "Untitled Database")
        markdown_lines.append(f"{indent}🗂️ [{title}](notion://database/{block['id']})")

    elif block_type == "table":
        # Tables are complex - for now just indicate there's a table
        markdown_lines.append(
            f"{indent}[Table with {block['table'].get('table_width', 0)} columns]"
        )

    elif block_type == "column_list":
        # Process columns
        if block.get("children"):
            markdown_lines.append(f"{indent}<div style='display: flex'>")
            for column in block["children"]:
                markdown_lines.append(f"{indent}<div style='flex: 1'>")
                if column.get("children"):
                    for child in column["children"]:
                        child_markdown = block_to_markdown(child, indent_level + 1)
                        if child_markdown:
                            markdown_lines.append(child_markdown)
                markdown_lines.append(f"{indent}</div>")
            markdown_lines.append(f"{indent}</div>")

    # Handle children for blocks that haven't been processed yet
    elif block.get("children") and block_type not in ["toggle", "column_list"]:
        for child in block["children"]:
            child_markdown = block_to_markdown(child, indent_level)
            if child_markdown:
                markdown_lines.append(child_markdown)

    return "\n".join(markdown_lines) if markdown_lines else ""