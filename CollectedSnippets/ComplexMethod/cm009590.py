def _iter_blocks() -> Iterator[types.ContentBlock]:
        for block in message.content:
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

            elif block_type == "reasoning_content":
                reasoning_block: types.ReasoningContentBlock = {"type": "reasoning"}
                if reasoning_content := block.get("reasoning_content"):
                    if reasoning := reasoning_content.get("text"):
                        reasoning_block["reasoning"] = reasoning
                    if signature := reasoning_content.get("signature"):
                        if "extras" not in reasoning_block:
                            reasoning_block["extras"] = {}
                        reasoning_block["extras"]["signature"] = signature

                if "index" in block:
                    reasoning_block["index"] = block["index"]

                known_fields = {"type", "reasoning_content", "index", "extras"}
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
                    yield tool_call_block

            elif (
                block_type == "input_json_delta"
                and isinstance(message, AIMessageChunk)
                and len(message.tool_call_chunks) == 1
            ):
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
                new_block: types.NonStandardContentBlock = {
                    "type": "non_standard",
                    "value": block,
                }
                if "index" in new_block["value"]:
                    new_block["index"] = new_block["value"].pop("index")
                yield new_block