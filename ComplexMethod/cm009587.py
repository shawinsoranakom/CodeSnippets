def _iter_blocks() -> Iterator[types.ContentBlock]:
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")

            if block_type == "text":
                if citations := block.get("citations"):
                    text_block: types.TextContentBlock = {
                        "type": "text",
                        "text": block.get("text", ""),
                        "annotations": [_convert_citation_to_v1(a) for a in citations],
                    }
                else:
                    text_block = {"type": "text", "text": block["text"]}
                if "index" in block:
                    text_block["index"] = block["index"]
                yield text_block

            elif block_type == "thinking":
                reasoning_block: types.ReasoningContentBlock = {
                    "type": "reasoning",
                    "reasoning": block.get("thinking", ""),
                }
                if "index" in block:
                    reasoning_block["index"] = block["index"]
                known_fields = {"type", "thinking", "index", "extras"}
                for key in block:
                    if key not in known_fields:
                        if "extras" not in reasoning_block:
                            reasoning_block["extras"] = {}
                        reasoning_block["extras"][key] = block[key]
                yield reasoning_block

            elif block_type == "tool_use":
                if (
                    isinstance(message, AIMessageChunk)
                    and len(message.tool_call_chunks) == 1
                    and message.chunk_position != "last"
                ):
                    # Isolated chunk
                    chunk = message.tool_call_chunks[0]

                    tool_call_chunk = types.ToolCallChunk(
                        name=chunk.get("name"),
                        id=chunk.get("id"),
                        args=chunk.get("args"),
                        type="tool_call_chunk",
                    )
                    if "caller" in block:
                        tool_call_chunk["extras"] = {"caller": block["caller"]}

                    index = chunk.get("index")
                    if index is not None:
                        tool_call_chunk["index"] = index
                    yield tool_call_chunk
                else:
                    tool_call_block: types.ToolCall | None = None
                    # Non-streaming or gathered chunk
                    if len(message.tool_calls) == 1:
                        tool_call_block = {
                            "type": "tool_call",
                            "name": message.tool_calls[0]["name"],
                            "args": message.tool_calls[0]["args"],
                            "id": message.tool_calls[0].get("id"),
                        }
                    elif call_id := block.get("id"):
                        for tc in message.tool_calls:
                            if tc.get("id") == call_id:
                                tool_call_block = {
                                    "type": "tool_call",
                                    "name": tc["name"],
                                    "args": tc["args"],
                                    "id": tc.get("id"),
                                }
                                break
                    if not tool_call_block:
                        tool_call_block = {
                            "type": "tool_call",
                            "name": block.get("name", ""),
                            "args": block.get("input", {}),
                            "id": block.get("id", ""),
                        }
                    if "index" in block:
                        tool_call_block["index"] = block["index"]
                    if "caller" in block:
                        if "extras" not in tool_call_block:
                            tool_call_block["extras"] = {}
                        tool_call_block["extras"]["caller"] = block["caller"]

                    yield tool_call_block

            elif block_type == "input_json_delta" and isinstance(
                message, AIMessageChunk
            ):
                if len(message.tool_call_chunks) == 1:
                    chunk = message.tool_call_chunks[0]
                    tool_call_chunk = types.ToolCallChunk(
                        name=chunk.get("name"),
                        id=chunk.get("id"),
                        args=chunk.get("args"),
                        type="tool_call_chunk",
                    )
                    index = chunk.get("index")
                    if index is not None:
                        tool_call_chunk["index"] = index
                    yield tool_call_chunk

                else:
                    server_tool_call_chunk: types.ServerToolCallChunk = {
                        "type": "server_tool_call_chunk",
                        "args": block.get("partial_json", ""),
                    }
                    if "index" in block:
                        server_tool_call_chunk["index"] = block["index"]
                    yield server_tool_call_chunk

            elif block_type == "server_tool_use":
                if block.get("name") == "code_execution":
                    server_tool_use_name = "code_interpreter"
                else:
                    server_tool_use_name = block.get("name", "")
                if (
                    isinstance(message, AIMessageChunk)
                    and block.get("input") == {}
                    and "partial_json" not in block
                    and message.chunk_position != "last"
                ):
                    # First chunk in a stream
                    server_tool_call_chunk = {
                        "type": "server_tool_call_chunk",
                        "name": server_tool_use_name,
                        "args": "",
                        "id": block.get("id", ""),
                    }
                    if "index" in block:
                        server_tool_call_chunk["index"] = block["index"]
                    known_fields = {"type", "name", "input", "id", "index"}
                    _populate_extras(server_tool_call_chunk, block, known_fields)
                    yield server_tool_call_chunk
                else:
                    server_tool_call: types.ServerToolCall = {
                        "type": "server_tool_call",
                        "name": server_tool_use_name,
                        "args": block.get("input", {}),
                        "id": block.get("id", ""),
                    }

                    if block.get("input") == {} and "partial_json" in block:
                        try:
                            input_ = json.loads(block["partial_json"])
                            if isinstance(input_, dict):
                                server_tool_call["args"] = input_
                        except json.JSONDecodeError:
                            pass

                    if "index" in block:
                        server_tool_call["index"] = block["index"]
                    known_fields = {
                        "type",
                        "name",
                        "input",
                        "partial_json",
                        "id",
                        "index",
                    }
                    _populate_extras(server_tool_call, block, known_fields)

                    yield server_tool_call

            elif block_type == "mcp_tool_use":
                if (
                    isinstance(message, AIMessageChunk)
                    and block.get("input") == {}
                    and "partial_json" not in block
                    and message.chunk_position != "last"
                ):
                    # First chunk in a stream
                    server_tool_call_chunk = {
                        "type": "server_tool_call_chunk",
                        "name": "remote_mcp",
                        "args": "",
                        "id": block.get("id", ""),
                    }
                    if "name" in block:
                        server_tool_call_chunk["extras"] = {"tool_name": block["name"]}
                    known_fields = {"type", "name", "input", "id", "index"}
                    _populate_extras(server_tool_call_chunk, block, known_fields)
                    if "index" in block:
                        server_tool_call_chunk["index"] = block["index"]
                    yield server_tool_call_chunk
                else:
                    server_tool_call = {
                        "type": "server_tool_call",
                        "name": "remote_mcp",
                        "args": block.get("input", {}),
                        "id": block.get("id", ""),
                    }

                    if block.get("input") == {} and "partial_json" in block:
                        try:
                            input_ = json.loads(block["partial_json"])
                            if isinstance(input_, dict):
                                server_tool_call["args"] = input_
                        except json.JSONDecodeError:
                            pass

                    if "name" in block:
                        server_tool_call["extras"] = {"tool_name": block["name"]}
                    known_fields = {
                        "type",
                        "name",
                        "input",
                        "partial_json",
                        "id",
                        "index",
                    }
                    _populate_extras(server_tool_call, block, known_fields)
                    if "index" in block:
                        server_tool_call["index"] = block["index"]

                    yield server_tool_call

            elif block_type and block_type.endswith("_tool_result"):
                server_tool_result: types.ServerToolResult = {
                    "type": "server_tool_result",
                    "tool_call_id": block.get("tool_use_id", ""),
                    "status": "success",
                    "extras": {"block_type": block_type},
                }
                if output := block.get("content", []):
                    server_tool_result["output"] = output
                    if isinstance(output, dict) and output.get(
                        "error_code"  # web_search, code_interpreter
                    ):
                        server_tool_result["status"] = "error"
                if block.get("is_error"):  # mcp_tool_result
                    server_tool_result["status"] = "error"
                if "index" in block:
                    server_tool_result["index"] = block["index"]

                known_fields = {"type", "tool_use_id", "content", "is_error", "index"}
                _populate_extras(server_tool_result, block, known_fields)

                yield server_tool_result

            else:
                new_block: types.NonStandardContentBlock = {
                    "type": "non_standard",
                    "value": block,
                }
                if "index" in new_block["value"]:
                    new_block["index"] = new_block["value"].pop("index")
                yield new_block