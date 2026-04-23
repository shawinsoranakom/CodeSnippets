def _markdown_to_blocks(content: str) -> List[dict]:
        """Convert markdown content to Notion block objects."""
        if not content:
            return []

        blocks = []
        lines = content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # Skip empty lines
            if not line.strip():
                i += 1
                continue

            # Headings
            if line.startswith("### "):
                blocks.append(
                    {
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [
                                {"type": "text", "text": {"content": line[4:].strip()}}
                            ]
                        },
                    }
                )
            elif line.startswith("## "):
                blocks.append(
                    {
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {"type": "text", "text": {"content": line[3:].strip()}}
                            ]
                        },
                    }
                )
            elif line.startswith("# "):
                blocks.append(
                    {
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [
                                {"type": "text", "text": {"content": line[2:].strip()}}
                            ]
                        },
                    }
                )
            # Bullet points
            elif line.strip().startswith("- "):
                blocks.append(
                    {
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": line.strip()[2:].strip()},
                                }
                            ]
                        },
                    }
                )
            # Numbered list
            elif line.strip() and line.strip()[0].isdigit() and ". " in line:
                content_start = line.find(". ") + 2
                blocks.append(
                    {
                        "type": "numbered_list_item",
                        "numbered_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": line[content_start:].strip()},
                                }
                            ]
                        },
                    }
                )
            # Code block
            elif line.strip().startswith("```"):
                code_lines = []
                language = line[3:].strip() or "plain text"
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                blocks.append(
                    {
                        "type": "code",
                        "code": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "\n".join(code_lines)},
                                }
                            ],
                            "language": language,
                        },
                    }
                )
            # Quote
            elif line.strip().startswith("> "):
                blocks.append(
                    {
                        "type": "quote",
                        "quote": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": line.strip()[2:].strip()},
                                }
                            ]
                        },
                    }
                )
            # Horizontal rule
            elif line.strip() in ["---", "***", "___"]:
                blocks.append({"type": "divider", "divider": {}})
            # Regular paragraph
            else:
                # Parse for basic markdown formatting
                text_content = line.strip()
                rich_text = []

                # Simple bold/italic parsing (this is simplified)
                if "**" in text_content or "*" in text_content:
                    # For now, just pass as plain text
                    # A full implementation would parse and create proper annotations
                    rich_text = [{"type": "text", "text": {"content": text_content}}]
                else:
                    rich_text = [{"type": "text", "text": {"content": text_content}}]

                blocks.append(
                    {"type": "paragraph", "paragraph": {"rich_text": rich_text}}
                )

            i += 1

        return blocks