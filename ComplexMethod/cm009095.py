def _construct_responses_api_input(messages: Sequence[BaseMessage]) -> list:
    """Construct the input for the OpenAI Responses API."""
    input_ = []
    for lc_msg in messages:
        if isinstance(lc_msg, AIMessage):
            lc_msg = _convert_from_v03_ai_message(lc_msg)
            msg = _convert_message_to_dict(lc_msg, api="responses")
            if isinstance(msg.get("content"), list) and all(
                isinstance(block, dict) for block in msg["content"]
            ):
                tcs: list[types.ToolCall] = [
                    {
                        "type": "tool_call",
                        "name": tool_call["name"],
                        "args": tool_call["args"],
                        "id": tool_call.get("id"),
                    }
                    for tool_call in lc_msg.tool_calls
                ]
                msg["content"] = _convert_from_v1_to_responses(msg["content"], tcs)
        else:
            msg = _convert_message_to_dict(lc_msg, api="responses")
            # Get content from non-standard content blocks
            if isinstance(msg["content"], list):
                for i, block in enumerate(msg["content"]):
                    if isinstance(block, dict) and block.get("type") == "non_standard":
                        msg["content"][i] = block["value"]
        # "name" parameter unsupported
        if "name" in msg:
            msg.pop("name")
        if msg["role"] == "tool":
            tool_output = msg["content"]
            computer_call_output = _make_computer_call_output_from_message(
                cast(ToolMessage, lc_msg)
            )
            custom_tool_output = _make_custom_tool_output_from_message(lc_msg)  # type: ignore[arg-type]
            if computer_call_output:
                input_.append(computer_call_output)
            elif custom_tool_output:
                input_.append(custom_tool_output)
            else:
                tool_output = _ensure_valid_tool_message_content(tool_output)
                function_call_output = {
                    "type": "function_call_output",
                    "output": tool_output,
                    "call_id": msg["tool_call_id"],
                }
                input_.append(function_call_output)
        elif msg["role"] == "assistant":
            if isinstance(msg.get("content"), list):
                for block in msg["content"]:
                    if isinstance(block, dict) and (block_type := block.get("type")):
                        # Aggregate content blocks for a single message
                        if block_type in ("text", "output_text", "refusal"):
                            msg_id = block.get("id")
                            phase = block.get("phase")
                            if block_type in ("text", "output_text"):
                                # Defensive check: block may not have "text" key
                                text = block.get("text")
                                if text is None:
                                    # Skip blocks without text content
                                    continue
                                new_block = {
                                    "type": "output_text",
                                    "text": text,
                                    "annotations": [
                                        _format_annotation_from_lc(annotation)
                                        for annotation in block.get("annotations") or []
                                    ],
                                }
                            elif block_type == "refusal":
                                new_block = {
                                    "type": "refusal",
                                    "refusal": block["refusal"],
                                }
                            for item in input_:
                                if (item_id := item.get("id")) and item_id == msg_id:
                                    # If existing block with this ID, append to it
                                    if "content" not in item:
                                        item["content"] = []
                                    item["content"].append(new_block)
                                    if phase is not None:
                                        item["phase"] = phase
                                    break
                            else:
                                # If no block with this ID, create a new one
                                new_item: dict = {
                                    "type": "message",
                                    "content": [new_block],
                                    "role": "assistant",
                                    "id": msg_id,
                                }
                                if phase is not None:
                                    new_item["phase"] = phase
                                input_.append(new_item)
                        elif block_type in (
                            "reasoning",
                            "compaction",
                            "web_search_call",
                            "file_search_call",
                            "function_call",
                            "computer_call",
                            "custom_tool_call",
                            "code_interpreter_call",
                            "mcp_call",
                            "mcp_list_tools",
                            "mcp_approval_request",
                            "tool_search_call",
                            "tool_search_output",
                        ):
                            input_.append(_pop_index_and_sub_index(block))
                        elif block_type == "image_generation_call":
                            # A previous image generation call can be referenced by ID
                            input_.append(
                                {"type": "image_generation_call", "id": block["id"]}
                            )
                        else:
                            pass
            elif isinstance(msg.get("content"), str):
                input_.append(
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [
                            {
                                "type": "output_text",
                                "text": msg["content"],
                                "annotations": [],
                            }
                        ],
                    }
                )

            # Add function calls from tool calls if not already present
            if tool_calls := msg.pop("tool_calls", None):
                content_call_ids = {
                    block["call_id"]
                    for block in input_
                    if block.get("type") in ("function_call", "custom_tool_call")
                    and "call_id" in block
                }
                for tool_call in tool_calls:
                    if tool_call["id"] not in content_call_ids:
                        function_call = {
                            "type": "function_call",
                            "name": tool_call["function"]["name"],
                            "arguments": tool_call["function"]["arguments"],
                            "call_id": tool_call["id"],
                        }
                        input_.append(function_call)

        elif msg["role"] in ("user", "system", "developer"):
            if isinstance(msg["content"], list):
                new_blocks = []
                non_message_item_types = ("mcp_approval_response", "tool_search_output")
                for block in msg["content"]:
                    if block["type"] in ("text", "image_url", "file"):
                        new_blocks.append(
                            _convert_chat_completions_blocks_to_responses(block)
                        )
                    elif block["type"] in ("input_text", "input_image", "input_file"):
                        new_blocks.append(block)
                    elif block["type"] in non_message_item_types:
                        input_.append(block)
                    else:
                        pass
                msg["content"] = new_blocks
                if msg["content"]:
                    msg["type"] = "message"
                    input_.append(msg)
            else:
                msg["type"] = "message"
                input_.append(msg)
        else:
            input_.append(msg)

    return input_