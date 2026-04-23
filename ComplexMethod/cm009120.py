def _convert_from_v1_to_responses(
    content: list[types.ContentBlock], tool_calls: list[types.ToolCall]
) -> list[dict[str, Any]]:
    new_content: list = []
    for block in content:
        if "type" not in block:
            continue
        if block["type"] == "text" and "annotations" in block:
            # Need a copy because we're changing the annotations list
            new_block = dict(block)
            new_block["annotations"] = [
                _convert_annotation_from_v1(a) for a in block["annotations"]
            ]
            new_content.append(new_block)
        elif block["type"] == "tool_call":
            new_block = {"type": "function_call", "call_id": block["id"]}
            if "extras" in block and "item_id" in block["extras"]:
                new_block["id"] = block["extras"]["item_id"]
            if "name" in block:
                new_block["name"] = block["name"]
            if "extras" in block and "arguments" in block["extras"]:
                new_block["arguments"] = block["extras"]["arguments"]
            if any(key not in new_block for key in ("name", "arguments")):
                matching_tool_calls = [
                    call for call in tool_calls if call["id"] == block["id"]
                ]
                if matching_tool_calls:
                    tool_call = matching_tool_calls[0]
                    if "name" not in new_block:
                        new_block["name"] = tool_call["name"]
                    if "arguments" not in new_block:
                        new_block["arguments"] = json.dumps(
                            tool_call["args"], separators=(",", ":")
                        )
            if "extras" in block:
                for extra_key in ("status", "namespace"):
                    if extra_key in block["extras"]:
                        new_block[extra_key] = block["extras"][extra_key]
            new_content.append(new_block)

        elif block["type"] == "server_tool_call" and block.get("name") == "tool_search":
            extras = block.get("extras", {})
            new_block = {"id": block["id"]}
            status = extras.get("status")
            if status:
                new_block["status"] = status
            new_block["type"] = "tool_search_call"
            if "args" in block:
                new_block["arguments"] = block["args"]
            execution = extras.get("execution")
            if execution:
                new_block["execution"] = execution
            new_content.append(new_block)

        elif (
            block["type"] == "server_tool_result"
            and block.get("extras", {}).get("name") == "tool_search"
        ):
            extras = block.get("extras", {})
            new_block = {"id": block.get("tool_call_id", "")}
            status = block.get("status")
            if status == "success":
                new_block["status"] = "completed"
            elif status == "error":
                new_block["status"] = "failed"
            elif status:
                new_block["status"] = status
            new_block["type"] = "tool_search_output"
            new_block["execution"] = "server"
            output: dict = block.get("output", {})
            if isinstance(output, dict) and "tools" in output:
                new_block["tools"] = output["tools"]
            new_content.append(new_block)

        elif (
            is_data_content_block(cast(dict, block))
            and block["type"] == "image"
            and "base64" in block
            and isinstance(block.get("id"), str)
            and block["id"].startswith("ig_")
        ):
            new_block = {"type": "image_generation_call", "result": block["base64"]}
            for extra_key in ("id", "status"):
                if extra_key in block:
                    new_block[extra_key] = block[extra_key]  # type: ignore[literal-required]
                elif extra_key in block.get("extras", {}):
                    new_block[extra_key] = block["extras"][extra_key]
            new_content.append(new_block)
        elif block["type"] == "non_standard" and "value" in block:
            new_content.append(block["value"])
        else:
            new_content.append(block)

    new_content = list(_implode_reasoning_blocks(new_content))
    return list(_consolidate_calls(new_content))