def _convert_to_v1_from_mistral(message: AIMessage) -> list[types.ContentBlock]:
    """Convert mistral message content to v1 format."""
    if isinstance(message.content, str):
        content_blocks: list[types.ContentBlock] = [
            {"type": "text", "text": message.content}
        ]

    else:
        content_blocks = []
        for block in message.content:
            if isinstance(block, str):
                content_blocks.append({"type": "text", "text": block})

            elif isinstance(block, dict):
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    text_block: types.TextContentBlock = {
                        "type": "text",
                        "text": block["text"],
                    }
                    if "index" in block:
                        text_block["index"] = block["index"]
                    content_blocks.append(text_block)

                elif block.get("type") == "thinking" and isinstance(
                    block.get("thinking"), list
                ):
                    for sub_block in block["thinking"]:
                        if (
                            isinstance(sub_block, dict)
                            and sub_block.get("type") == "text"
                        ):
                            reasoning_block: types.ReasoningContentBlock = {
                                "type": "reasoning",
                                "reasoning": sub_block.get("text", ""),
                            }
                            if "index" in block:
                                reasoning_block["index"] = block["index"]
                            content_blocks.append(reasoning_block)

                else:
                    non_standard_block: types.NonStandardContentBlock = {
                        "type": "non_standard",
                        "value": block,
                    }
                    content_blocks.append(non_standard_block)
            else:
                continue

    if (
        len(content_blocks) == 1
        and content_blocks[0].get("type") == "text"
        and content_blocks[0].get("text") == ""
        and message.tool_calls
    ):
        content_blocks = []

    for tool_call in message.tool_calls:
        content_blocks.append(
            {
                "type": "tool_call",
                "name": tool_call["name"],
                "args": tool_call["args"],
                "id": tool_call.get("id"),
            }
        )

    return content_blocks