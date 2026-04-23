def _make_custom_tool_output_from_message(message: ToolMessage) -> dict | None:
    custom_tool_output = None
    for block in message.content:
        if isinstance(block, dict) and block.get("type") == "custom_tool_call_output":
            custom_tool_output = {
                "type": "custom_tool_call_output",
                "call_id": message.tool_call_id,
                "output": block.get("output") or "",
            }
            break
        if (
            isinstance(block, dict)
            and block.get("type") == "non_standard"
            and block.get("value", {}).get("type") == "custom_tool_call_output"
        ):
            custom_tool_output = block["value"]
            break

    return custom_tool_output