def _convert_to_v1_from_groq(message: AIMessage) -> list[types.ContentBlock]:
    """Convert groq message content to v1 format."""
    content_blocks: list[types.ContentBlock] = []

    if reasoning_block := _extract_reasoning_from_additional_kwargs(message):
        content_blocks.append(reasoning_block)

    if executed_tools := message.additional_kwargs.get("executed_tools"):
        for idx, executed_tool in enumerate(executed_tools):
            args: dict[str, Any] | None = None
            if arguments := executed_tool.get("arguments"):
                try:
                    args = json.loads(arguments)
                except json.JSONDecodeError:
                    if executed_tool.get("type") == "python":
                        try:
                            args = _parse_code_json(arguments)
                        except ValueError:
                            continue
                    elif (
                        executed_tool.get("type") == "function"
                        and executed_tool.get("name") == "python"
                    ):
                        # GPT-OSS
                        args = {"code": arguments}
                    else:
                        continue
            if isinstance(args, dict):
                name = ""
                if executed_tool.get("type") == "search":
                    name = "web_search"
                elif executed_tool.get("type") == "python" or (
                    executed_tool.get("type") == "function"
                    and executed_tool.get("name") == "python"
                ):
                    name = "code_interpreter"
                server_tool_call: types.ServerToolCall = {
                    "type": "server_tool_call",
                    "name": name,
                    "id": str(idx),
                    "args": args,
                }
                content_blocks.append(server_tool_call)
            if tool_output := executed_tool.get("output"):
                tool_result: types.ServerToolResult = {
                    "type": "server_tool_result",
                    "tool_call_id": str(idx),
                    "output": tool_output,
                    "status": "success",
                }
                known_fields = {"type", "arguments", "index", "output"}
                _populate_extras(tool_result, executed_tool, known_fields)
                content_blocks.append(tool_result)

    if isinstance(message.content, str) and message.content:
        content_blocks.append({"type": "text", "text": message.content})

    content_blocks.extend(
        {
            "type": "tool_call",
            "name": tool_call["name"],
            "args": tool_call["args"],
            "id": tool_call.get("id"),
        }
        for tool_call in message.tool_calls
    )

    return content_blocks