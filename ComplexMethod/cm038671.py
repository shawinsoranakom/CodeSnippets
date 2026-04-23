def _convert_user_tool_result(
        cls, block, openai_messages: list[dict[str, Any]]
    ) -> None:
        """Convert user tool_result with text and image support"""
        tool_text = ""
        tool_image_urls: list[str] = []

        if isinstance(block.content, str):
            tool_text = block.content
        elif isinstance(block.content, list):
            text_parts: list[str] = []
            for item in block.content:
                if not isinstance(item, dict):
                    continue
                item_type = item.get("type")
                if item_type == "text":
                    text_parts.append(item.get("text", ""))
                elif item_type == "image":
                    source = item.get("source", {})
                    url = cls._convert_image_source_to_url(source)
                    if url:
                        tool_image_urls.append(url)
            tool_text = "\n".join(text_parts)

        openai_messages.append(
            {
                "role": "tool",
                "tool_call_id": block.tool_use_id or "",
                "content": tool_text or "",
            }
        )

        if tool_image_urls:
            openai_messages.append(
                {
                    "role": "user",
                    "content": [  # type: ignore[dict-item]
                        {"type": "image_url", "image_url": {"url": img}}
                        for img in tool_image_urls
                    ],
                }
            )