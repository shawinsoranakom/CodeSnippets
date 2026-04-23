def _iter_blocks() -> Iterator[types.ContentBlock]:
        for raw_block in message.content:
            if not isinstance(raw_block, dict):
                continue
            block = raw_block.copy()
            block_type = block.get("type")

            if block_type == "text":
                if "text" not in block:
                    block["text"] = ""
                if "annotations" in block:
                    block["annotations"] = [
                        _convert_annotation_to_v1(a) for a in block["annotations"]
                    ]
                if "index" in block:
                    block["index"] = f"lc_txt_{block['index']}"
                yield cast("types.TextContentBlock", block)

            elif block_type == "reasoning":
                yield from _explode_reasoning(block)

            elif block_type == "image_generation_call" and (
                result := block.get("result")
            ):
                new_block = {"type": "image", "base64": result}
                if output_format := block.get("output_format"):
                    new_block["mime_type"] = f"image/{output_format}"
                if "id" in block:
                    new_block["id"] = block["id"]
                if "index" in block:
                    new_block["index"] = f"lc_img_{block['index']}"
                for extra_key in (
                    "status",
                    "background",
                    "output_format",
                    "quality",
                    "revised_prompt",
                    "size",
                ):
                    if extra_key in block:
                        if "extras" not in new_block:
                            new_block["extras"] = {}
                        new_block["extras"][extra_key] = block[extra_key]
                yield cast("types.ImageContentBlock", new_block)

            elif block_type == "function_call":
                tool_call_block: (
                    types.ToolCall | types.InvalidToolCall | types.ToolCallChunk | None
                ) = None
                call_id = block.get("call_id", "")

                if (
                    isinstance(message, AIMessageChunk)
                    and len(message.tool_call_chunks) == 1
                    and message.chunk_position != "last"
                ):
                    tool_call_block = message.tool_call_chunks[0].copy()  # type: ignore[assignment]
                elif call_id:
                    for tool_call in message.tool_calls or []:
                        if tool_call.get("id") == call_id:
                            tool_call_block = {
                                "type": "tool_call",
                                "name": tool_call["name"],
                                "args": tool_call["args"],
                                "id": tool_call.get("id"),
                            }
                            break
                    else:
                        for invalid_tool_call in message.invalid_tool_calls or []:
                            if invalid_tool_call.get("id") == call_id:
                                tool_call_block = invalid_tool_call.copy()
                                break
                if tool_call_block:
                    if "id" in block:
                        if "extras" not in tool_call_block:
                            tool_call_block["extras"] = {}
                        tool_call_block["extras"]["item_id"] = block["id"]
                    if "index" in block:
                        tool_call_block["index"] = f"lc_tc_{block['index']}"
                    for extra_key in ("status", "namespace"):
                        if extra_key in block:
                            if "extras" not in tool_call_block:
                                tool_call_block["extras"] = {}
                            tool_call_block["extras"][extra_key] = block[extra_key]
                    yield tool_call_block

            elif block_type == "web_search_call":
                web_search_call = {
                    "type": "server_tool_call",
                    "name": "web_search",
                    "args": {},
                    "id": block["id"],
                }
                if "index" in block:
                    web_search_call["index"] = f"lc_wsc_{block['index']}"

                sources: dict[str, Any] | None = None
                if "action" in block and isinstance(block["action"], dict):
                    if "sources" in block["action"]:
                        sources = block["action"]["sources"]
                    web_search_call["args"] = {
                        k: v for k, v in block["action"].items() if k != "sources"
                    }
                for key in block:
                    if key not in {"type", "id", "action", "status", "index"}:
                        web_search_call[key] = block[key]

                yield cast("types.ServerToolCall", web_search_call)

                # If .content already has web_search_result, don't add
                if not any(
                    isinstance(other_block, dict)
                    and other_block.get("type") == "web_search_result"
                    and other_block.get("id") == block["id"]
                    for other_block in message.content
                ):
                    web_search_result = {
                        "type": "server_tool_result",
                        "tool_call_id": block["id"],
                    }
                    if sources:
                        web_search_result["output"] = {"sources": sources}

                    status = block.get("status")
                    if status == "failed":
                        web_search_result["status"] = "error"
                    elif status == "completed":
                        web_search_result["status"] = "success"
                    elif status:
                        web_search_result["extras"] = {"status": status}
                    if "index" in block and isinstance(block["index"], int):
                        web_search_result["index"] = f"lc_wsr_{block['index'] + 1}"
                    yield cast("types.ServerToolResult", web_search_result)

            elif block_type == "file_search_call":
                file_search_call = {
                    "type": "server_tool_call",
                    "name": "file_search",
                    "id": block["id"],
                    "args": {"queries": block.get("queries", [])},
                }
                if "index" in block:
                    file_search_call["index"] = f"lc_fsc_{block['index']}"

                for key in block:
                    if key not in {
                        "type",
                        "id",
                        "queries",
                        "results",
                        "status",
                        "index",
                    }:
                        file_search_call[key] = block[key]

                yield cast("types.ServerToolCall", file_search_call)

                file_search_result = {
                    "type": "server_tool_result",
                    "tool_call_id": block["id"],
                }
                if file_search_output := block.get("results"):
                    file_search_result["output"] = file_search_output

                status = block.get("status")
                if status == "failed":
                    file_search_result["status"] = "error"
                elif status == "completed":
                    file_search_result["status"] = "success"
                elif status:
                    file_search_result["extras"] = {"status": status}
                if "index" in block and isinstance(block["index"], int):
                    file_search_result["index"] = f"lc_fsr_{block['index'] + 1}"
                yield cast("types.ServerToolResult", file_search_result)

            elif block_type == "code_interpreter_call":
                code_interpreter_call = {
                    "type": "server_tool_call",
                    "name": "code_interpreter",
                    "id": block["id"],
                }
                if "code" in block:
                    code_interpreter_call["args"] = {"code": block["code"]}
                if "index" in block:
                    code_interpreter_call["index"] = f"lc_cic_{block['index']}"
                known_fields = {
                    "type",
                    "id",
                    "outputs",
                    "status",
                    "code",
                    "extras",
                    "index",
                }
                for key in block:
                    if key not in known_fields:
                        if "extras" not in code_interpreter_call:
                            code_interpreter_call["extras"] = {}
                        code_interpreter_call["extras"][key] = block[key]

                code_interpreter_result = {
                    "type": "server_tool_result",
                    "tool_call_id": block["id"],
                }
                if "outputs" in block:
                    code_interpreter_result["output"] = block["outputs"]

                status = block.get("status")
                if status == "failed":
                    code_interpreter_result["status"] = "error"
                elif status == "completed":
                    code_interpreter_result["status"] = "success"
                elif status:
                    code_interpreter_result["extras"] = {"status": status}
                if "index" in block and isinstance(block["index"], int):
                    code_interpreter_result["index"] = f"lc_cir_{block['index'] + 1}"

                yield cast("types.ServerToolCall", code_interpreter_call)
                yield cast("types.ServerToolResult", code_interpreter_result)

            elif block_type == "mcp_call":
                mcp_call = {
                    "type": "server_tool_call",
                    "name": "remote_mcp",
                    "id": block["id"],
                }
                if (arguments := block.get("arguments")) and isinstance(arguments, str):
                    try:
                        mcp_call["args"] = json.loads(block["arguments"])
                    except json.JSONDecodeError:
                        mcp_call["extras"] = {"arguments": arguments}
                if "name" in block:
                    if "extras" not in mcp_call:
                        mcp_call["extras"] = {}
                    mcp_call["extras"]["tool_name"] = block["name"]
                if "server_label" in block:
                    if "extras" not in mcp_call:
                        mcp_call["extras"] = {}
                    mcp_call["extras"]["server_label"] = block["server_label"]
                if "index" in block:
                    mcp_call["index"] = f"lc_mcp_{block['index']}"
                known_fields = {
                    "type",
                    "id",
                    "arguments",
                    "name",
                    "server_label",
                    "output",
                    "error",
                    "extras",
                    "index",
                }
                for key in block:
                    if key not in known_fields:
                        if "extras" not in mcp_call:
                            mcp_call["extras"] = {}
                        mcp_call["extras"][key] = block[key]

                yield cast("types.ServerToolCall", mcp_call)

                mcp_result = {
                    "type": "server_tool_result",
                    "tool_call_id": block["id"],
                }
                if mcp_output := block.get("output"):
                    mcp_result["output"] = mcp_output

                error = block.get("error")
                if error:
                    if "extras" not in mcp_result:
                        mcp_result["extras"] = {}
                    mcp_result["extras"]["error"] = error
                    mcp_result["status"] = "error"
                else:
                    mcp_result["status"] = "success"

                if "index" in block and isinstance(block["index"], int):
                    mcp_result["index"] = f"lc_mcpr_{block['index'] + 1}"
                yield cast("types.ServerToolResult", mcp_result)

            elif block_type == "mcp_list_tools":
                mcp_list_tools_call = {
                    "type": "server_tool_call",
                    "name": "mcp_list_tools",
                    "args": {},
                    "id": block["id"],
                }
                if "server_label" in block:
                    mcp_list_tools_call["extras"] = {}
                    mcp_list_tools_call["extras"]["server_label"] = block[
                        "server_label"
                    ]
                if "index" in block:
                    mcp_list_tools_call["index"] = f"lc_mlt_{block['index']}"
                known_fields = {
                    "type",
                    "id",
                    "name",
                    "server_label",
                    "tools",
                    "error",
                    "extras",
                    "index",
                }
                for key in block:
                    if key not in known_fields:
                        if "extras" not in mcp_list_tools_call:
                            mcp_list_tools_call["extras"] = {}
                        mcp_list_tools_call["extras"][key] = block[key]

                yield cast("types.ServerToolCall", mcp_list_tools_call)

                mcp_list_tools_result = {
                    "type": "server_tool_result",
                    "tool_call_id": block["id"],
                }
                if mcp_output := block.get("tools"):
                    mcp_list_tools_result["output"] = mcp_output

                error = block.get("error")
                if error:
                    if "extras" not in mcp_list_tools_result:
                        mcp_list_tools_result["extras"] = {}
                    mcp_list_tools_result["extras"]["error"] = error
                    mcp_list_tools_result["status"] = "error"
                else:
                    mcp_list_tools_result["status"] = "success"

                if "index" in block and isinstance(block["index"], int):
                    mcp_list_tools_result["index"] = f"lc_mltr_{block['index'] + 1}"
                yield cast("types.ServerToolResult", mcp_list_tools_result)

            elif (
                block_type == "tool_search_call" and block.get("execution") == "server"
            ):
                tool_search_call: dict[str, Any] = {
                    "type": "server_tool_call",
                    "name": "tool_search",
                    "id": block["id"],
                    "args": block.get("arguments", {}),
                }
                if "index" in block:
                    tool_search_call["index"] = f"lc_tsc_{block['index']}"
                extras: dict[str, Any] = {}
                known = {"type", "id", "arguments", "index"}
                for key in block:
                    if key not in known:
                        extras[key] = block[key]
                if extras:
                    tool_search_call["extras"] = extras
                yield cast("types.ServerToolCall", tool_search_call)

            elif (
                block_type == "tool_search_output"
                and block.get("execution") == "server"
            ):
                tool_search_output: dict[str, Any] = {
                    "type": "server_tool_result",
                    "tool_call_id": block["id"],
                    "output": {"tools": block.get("tools", [])},
                }
                status = block.get("status")
                if status == "failed":
                    tool_search_output["status"] = "error"
                elif status == "completed":
                    tool_search_output["status"] = "success"
                if "index" in block and isinstance(block["index"], int):
                    tool_search_output["index"] = f"lc_tso_{block['index']}"
                extras_out: dict[str, Any] = {"name": "tool_search"}
                known_out = {"type", "id", "status", "tools", "index"}
                for key in block:
                    if key not in known_out:
                        extras_out[key] = block[key]
                if extras_out:
                    tool_search_output["extras"] = extras_out
                yield cast("types.ServerToolResult", tool_search_output)

            elif block_type in types.KNOWN_BLOCK_TYPES:
                yield cast("types.ContentBlock", block)
            else:
                new_block = {"type": "non_standard", "value": block}
                if "index" in new_block["value"]:
                    new_block["index"] = f"lc_ns_{new_block['value'].pop('index')}"
                yield cast("types.NonStandardContentBlock", new_block)