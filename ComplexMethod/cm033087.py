def _parse_content_to_sections(self, content_data: list[dict[str, Any]]) -> list[tuple[str, str]]:
        """Convert parsing results to sections format"""
        sections = []

        for item in content_data:
            content_type = item.get("type", "text")
            content = item.get("content", "")

            if not content:
                continue

            # Process based on content type
            if content_type == "text" or content_type == "paragraph":
                section_text = content
            elif content_type == "table":
                # Handle table content
                table_data = item.get("table_data", {})
                if isinstance(table_data, dict):
                    # Convert table data to text
                    rows = table_data.get("rows", [])
                    section_text = "\n".join([" | ".join(row) for row in rows])
                else:
                    section_text = str(table_data)
            elif content_type == "image":
                # Handle image content
                caption = item.get("caption", "")
                section_text = f"[Image] {caption}" if caption else "[Image]"
            elif content_type == "equation":
                # Handle equation content
                section_text = f"$${content}$$"
            else:
                section_text = content

            if section_text.strip():
                # Generate position tag (simplified version)
                position_tag = "@@1\t0.0\t1000.0\t0.0\t100.0##"
                sections.append((section_text, position_tag))

        return sections