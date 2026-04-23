def create_block(self, block_type: str, content: str, **kwargs) -> dict[str, Any]:
        block: dict[str, Any] = {
            "object": "block",
            "type": block_type,
            block_type: {},
        }

        if block_type in {
            "paragraph",
            "heading_1",
            "heading_2",
            "heading_3",
            "bulleted_list_item",
            "numbered_list_item",
            "quote",
        }:
            block[block_type]["rich_text"] = [
                {
                    "type": "text",
                    "text": {
                        "content": content,
                    },
                }
            ]
        elif block_type == "to_do":
            block[block_type]["rich_text"] = [
                {
                    "type": "text",
                    "text": {
                        "content": content,
                    },
                }
            ]
            block[block_type]["checked"] = kwargs.get("checked", False)
        elif block_type == "code":
            block[block_type]["rich_text"] = [
                {
                    "type": "text",
                    "text": {
                        "content": content,
                    },
                }
            ]
            block[block_type]["language"] = kwargs.get("language", "plain text")
        elif block_type == "image":
            block[block_type] = {"type": "external", "external": {"url": kwargs.get("image_url", "")}}
        elif block_type == "divider":
            pass
        elif block_type == "bookmark":
            block[block_type]["url"] = kwargs.get("link_url", "")
        elif block_type == "table":
            block[block_type]["table_width"] = kwargs.get("table_width", 0)
            block[block_type]["has_column_header"] = kwargs.get("has_column_header", False)
            block[block_type]["has_row_header"] = kwargs.get("has_row_header", False)
        elif block_type == "table_row":
            block[block_type]["cells"] = [[{"type": "text", "text": {"content": cell}} for cell in content]]

        return block