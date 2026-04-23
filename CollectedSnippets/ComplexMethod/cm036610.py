def _accumulate_tool_states(delta_messages):
    """Accumulate tool call state from a stream of DeltaMessage objects."""
    content = ""
    tool_states = {}
    for delta_message in delta_messages:
        if delta_message.content:
            content += delta_message.content
        if delta_message.tool_calls:
            for tool_call in delta_message.tool_calls:
                idx = tool_call.index
                if idx not in tool_states:
                    tool_states[idx] = {
                        "id": None,
                        "name": None,
                        "arguments": "",
                        "type": None,
                    }
                if tool_call.id:
                    tool_states[idx]["id"] = tool_call.id
                if tool_call.type:
                    tool_states[idx]["type"] = tool_call.type
                if tool_call.function:
                    if tool_call.function.name:
                        tool_states[idx]["name"] = tool_call.function.name
                    if tool_call.function.arguments is not None:
                        tool_states[idx]["arguments"] += tool_call.function.arguments
    return content, tool_states