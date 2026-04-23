def _convert_block(
        cls,
        block,
        role: str,
        content_parts: list[dict[str, Any]],
        tool_calls: list[dict[str, Any]],
        reasoning_parts: list[str],
        openai_messages: list[dict[str, Any]],
    ) -> None:
        """Convert individual content block"""
        if block.type == "text" and block.text:
            content_parts.append({"type": "text", "text": block.text})
        elif block.type == "image" and block.source:
            image_url = cls._convert_image_source_to_url(block.source)
            content_parts.append({"type": "image_url", "image_url": {"url": image_url}})
        elif block.type == "thinking" and block.thinking is not None:
            reasoning_parts.append(block.thinking)
        elif block.type == "redacted_thinking":
            # Redacted thinking blocks contain safety-filtered reasoning.
            # We skip them as the content is opaque (base64 'data' field),
            # but accepting the block prevents a validation error when the
            # client echoes back the full assistant message.
            pass
        elif block.type == "tool_use":
            cls._convert_tool_use_block(block, tool_calls)
        elif block.type == "tool_result":
            cls._convert_tool_result_block(block, role, openai_messages, content_parts)