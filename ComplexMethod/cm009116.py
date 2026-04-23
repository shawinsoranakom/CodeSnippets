def _convert_to_v03_ai_message(
    message: AIMessage, has_reasoning: bool = False
) -> AIMessage:
    """Mutate an `AIMessage` to the old-style v0.3 format."""
    if isinstance(message.content, list):
        new_content: list[dict | str] = []
        for block in message.content:
            if isinstance(block, dict):
                if block.get("type") == "reasoning":
                    # Store a reasoning item in additional_kwargs (overwriting as in
                    # v0.3)
                    _ = block.pop("index", None)
                    if has_reasoning:
                        _ = block.pop("id", None)
                        _ = block.pop("type", None)
                    message.additional_kwargs["reasoning"] = block
                elif block.get("type") in (
                    "web_search_call",
                    "file_search_call",
                    "computer_call",
                    "code_interpreter_call",
                    "mcp_call",
                    "mcp_list_tools",
                    "mcp_approval_request",
                    "image_generation_call",
                    "tool_search_call",
                    "tool_search_output",
                ):
                    # Store built-in tool calls in additional_kwargs
                    if "tool_outputs" not in message.additional_kwargs:
                        message.additional_kwargs["tool_outputs"] = []
                    message.additional_kwargs["tool_outputs"].append(block)
                elif block.get("type") == "function_call":
                    # Store function call item IDs in additional_kwargs, otherwise
                    # discard function call items.
                    if _FUNCTION_CALL_IDS_MAP_KEY not in message.additional_kwargs:
                        message.additional_kwargs[_FUNCTION_CALL_IDS_MAP_KEY] = {}
                    if (call_id := block.get("call_id")) and (
                        function_call_id := block.get("id")
                    ):
                        message.additional_kwargs[_FUNCTION_CALL_IDS_MAP_KEY][
                            call_id
                        ] = function_call_id
                elif (block.get("type") == "refusal") and (
                    refusal := block.get("refusal")
                ):
                    # Store a refusal item in additional_kwargs (overwriting as in
                    # v0.3)
                    message.additional_kwargs["refusal"] = refusal
                elif block.get("type") == "text":
                    # Store a message item ID on AIMessage.id
                    if "id" in block:
                        message.id = block["id"]
                    new_content.append({k: v for k, v in block.items() if k != "id"})
                elif (
                    set(block.keys()) == {"id", "index"}
                    and isinstance(block["id"], str)
                    and block["id"].startswith("msg_")
                ):
                    # Drop message IDs in streaming case
                    new_content.append({"index": block["index"]})
                else:
                    new_content.append(block)
            else:
                new_content.append(block)
        message.content = new_content
        if isinstance(message.id, str) and message.id.startswith("resp_"):
            message.id = None
    else:
        pass

    return message