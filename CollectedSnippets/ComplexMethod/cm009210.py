def _merge_messages(
    messages: Sequence[BaseMessage],
) -> list[SystemMessage | AIMessage | HumanMessage]:
    """Merge runs of human/tool messages into single human messages with content blocks."""  # noqa: E501
    merged: list = []
    for curr in messages:
        if isinstance(curr, ToolMessage):
            if (
                isinstance(curr.content, list)
                and curr.content
                and all(
                    isinstance(block, dict) and block.get("type") == "tool_result"
                    for block in curr.content
                )
            ):
                curr = HumanMessage(curr.content)  # type: ignore[misc]
            else:
                tool_content = curr.content
                cache_ctrl = None
                # Extract cache_control from content blocks and hoist it
                # to the tool_result level.  Anthropic's API does not
                # support cache_control on tool_result content sub-blocks.
                if isinstance(tool_content, list):
                    cleaned = []
                    for block in tool_content:
                        if isinstance(block, dict) and "cache_control" in block:
                            cache_ctrl = block["cache_control"]
                            block = {
                                k: v for k, v in block.items() if k != "cache_control"
                            }
                        cleaned.append(block)
                    tool_content = cleaned
                tool_result: dict = {
                    "type": "tool_result",
                    "content": tool_content,
                    "tool_use_id": curr.tool_call_id,
                    "is_error": curr.status == "error",
                }
                if cache_ctrl:
                    tool_result["cache_control"] = cache_ctrl
                curr = HumanMessage(  # type: ignore[misc]
                    [tool_result],
                )
        last = merged[-1] if merged else None
        if any(
            all(isinstance(m, c) for m in (curr, last))
            for c in (SystemMessage, HumanMessage)
        ):
            if isinstance(cast("BaseMessage", last).content, str):
                new_content: list = [
                    {"type": "text", "text": cast("BaseMessage", last).content},
                ]
            else:
                new_content = copy.copy(cast("list", cast("BaseMessage", last).content))
            if isinstance(curr.content, str):
                new_content.append({"type": "text", "text": curr.content})
            else:
                new_content.extend(curr.content)
            merged[-1] = curr.model_copy(update={"content": new_content})
        else:
            merged.append(curr)
    return merged