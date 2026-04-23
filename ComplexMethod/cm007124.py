def parse_blocks(self, blocks: list) -> str:
        content = ""
        for block in blocks:
            block_type = block.get("type")
            if block_type in {"paragraph", "heading_1", "heading_2", "heading_3", "quote"}:
                content += self.parse_rich_text(block[block_type].get("rich_text", [])) + "\n\n"
            elif block_type in {"bulleted_list_item", "numbered_list_item"}:
                content += self.parse_rich_text(block[block_type].get("rich_text", [])) + "\n"
            elif block_type == "to_do":
                content += self.parse_rich_text(block["to_do"].get("rich_text", [])) + "\n"
            elif block_type == "code":
                content += self.parse_rich_text(block["code"].get("rich_text", [])) + "\n\n"
            elif block_type == "image":
                content += f"[Image: {block['image'].get('external', {}).get('url', 'No URL')}]\n\n"
            elif block_type == "divider":
                content += "---\n\n"
        return content.strip()