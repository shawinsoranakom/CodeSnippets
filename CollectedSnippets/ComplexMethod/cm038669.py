def _convert_message_content(
        cls,
        msg,
        openai_msg: dict[str, Any],
        openai_messages: list[dict[str, Any]],
    ) -> None:
        """Convert complex message content blocks"""
        content_parts: list[dict[str, Any]] = []
        tool_calls: list[dict[str, Any]] = []
        reasoning_parts: list[str] = []

        for block in msg.content:
            cls._convert_block(
                block,
                msg.role,
                content_parts,
                tool_calls,
                reasoning_parts,
                openai_messages,
            )

        if reasoning_parts:
            openai_msg["reasoning"] = "".join(reasoning_parts)

        if tool_calls:
            openai_msg["tool_calls"] = tool_calls  # type: ignore

        if content_parts:
            if len(content_parts) == 1 and content_parts[0]["type"] == "text":
                openai_msg["content"] = content_parts[0]["text"]
            else:
                openai_msg["content"] = content_parts  # type: ignore
        elif not tool_calls and not reasoning_parts:
            return