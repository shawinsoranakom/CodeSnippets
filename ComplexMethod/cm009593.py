def _convert_to_v1_from_genai(message: AIMessage) -> list[types.ContentBlock]:
    """Convert Google GenAI message content to v1 format.

    Calling `.content_blocks` on an `AIMessage` where `response_metadata.model_provider`
    is set to `'google_genai'` will invoke this function to parse the content into
    standard content blocks for returning.

    Args:
        message: The `AIMessage` or `AIMessageChunk` to convert.

    Returns:
        List of standard content blocks derived from the message content.
    """
    if isinstance(message.content, str):
        # String content -> TextContentBlock (only add if non-empty in case of audio)
        string_blocks: list[types.ContentBlock] = []
        if message.content:
            string_blocks.append({"type": "text", "text": message.content})

        # Add any missing tool calls from message.tool_calls field
        content_tool_call_ids = {
            block.get("id")
            for block in string_blocks
            if isinstance(block, dict) and block.get("type") == "tool_call"
        }
        for tool_call in message.tool_calls:
            id_ = tool_call.get("id")
            if id_ and id_ not in content_tool_call_ids:
                string_tool_call_block: types.ToolCall = {
                    "type": "tool_call",
                    "id": id_,
                    "name": tool_call["name"],
                    "args": tool_call["args"],
                }
                string_blocks.append(string_tool_call_block)

        # Handle audio from additional_kwargs if present (for empty content cases)
        audio_data = message.additional_kwargs.get("audio")
        if audio_data and isinstance(audio_data, bytes):
            audio_block: types.AudioContentBlock = {
                "type": "audio",
                "base64": _bytes_to_b64_str(audio_data),
                "mime_type": "audio/wav",  # Default to WAV for Google GenAI
            }
            string_blocks.append(audio_block)

        grounding_metadata = message.response_metadata.get("grounding_metadata")
        if grounding_metadata:
            citations = translate_grounding_metadata_to_citations(grounding_metadata)

            for block in string_blocks:
                if block["type"] == "text" and citations:
                    # Add citations to the first text block only
                    block["annotations"] = cast("list[types.Annotation]", citations)
                    break

        return string_blocks

    if not isinstance(message.content, list):
        # Unexpected content type, attempt to represent as text
        return [{"type": "text", "text": str(message.content)}]

    converted_blocks: list[types.ContentBlock] = []

    for item in message.content:
        if isinstance(item, str):
            # Conversation history strings

            # Citations are handled below after all blocks are converted
            converted_blocks.append({"type": "text", "text": item})  # TextContentBlock

        elif isinstance(item, dict):
            item_type = item.get("type")
            if item_type == "image_url":
                # Convert image_url to standard image block (base64)
                # (since the original implementation returned as url-base64 CC style)
                image_url = item.get("image_url", {})
                url = image_url.get("url", "")
                if url:
                    # Extract base64 data
                    match = re.match(r"data:([^;]+);base64,(.+)", url)
                    if match:
                        # Data URI provided
                        mime_type, base64_data = match.groups()
                        converted_blocks.append(
                            {
                                "type": "image",
                                "base64": base64_data,
                                "mime_type": mime_type,
                            }
                        )
                    else:
                        # Assume it's raw base64 without data URI
                        try:
                            # Validate base64 and decode for MIME type detection
                            decoded_bytes = base64.b64decode(url, validate=True)

                            image_url_b64_block = {
                                "type": "image",
                                "base64": url,
                            }

                            if _HAS_FILETYPE:
                                # Guess MIME type based on file bytes
                                mime_type = None
                                kind = filetype.guess(decoded_bytes)
                                if kind:
                                    mime_type = kind.mime
                                if mime_type:
                                    image_url_b64_block["mime_type"] = mime_type

                            converted_blocks.append(
                                cast("types.ImageContentBlock", image_url_b64_block)
                            )
                        except Exception:
                            # Not valid base64, treat as non-standard
                            converted_blocks.append(
                                {
                                    "type": "non_standard",
                                    "value": item,
                                }
                            )
                else:
                    # This likely won't be reached according to previous implementations
                    converted_blocks.append({"type": "non_standard", "value": item})
                    msg = "Image URL not a data URI; appending as non-standard block."
                    raise ValueError(msg)
            elif item_type == "function_call":
                # Handle Google GenAI function calls
                function_call_block: types.ToolCall = {
                    "type": "tool_call",
                    "name": item.get("name", ""),
                    "args": item.get("args", {}),
                    "id": item.get("id", ""),
                }
                converted_blocks.append(function_call_block)
            elif item_type == "file_data":
                # Handle FileData URI-based content
                file_block: types.FileContentBlock = {
                    "type": "file",
                    "url": item.get("file_uri", ""),
                }
                if mime_type := item.get("mime_type"):
                    file_block["mime_type"] = mime_type
                converted_blocks.append(file_block)
            elif item_type == "thinking":
                # Handling for the 'thinking' type we package thoughts as
                reasoning_block: types.ReasoningContentBlock = {
                    "type": "reasoning",
                    "reasoning": item.get("thinking", ""),
                }
                if signature := item.get("signature"):
                    reasoning_block["extras"] = {"signature": signature}

                converted_blocks.append(reasoning_block)
            elif item_type == "executable_code":
                # Convert to standard server tool call block at the moment
                server_tool_call_block: types.ServerToolCall = {
                    "type": "server_tool_call",
                    "name": "code_interpreter",
                    "args": {
                        "code": item.get("executable_code", ""),
                        "language": item.get("language", "python"),  # Default to python
                    },
                    "id": item.get("id", ""),
                }
                converted_blocks.append(server_tool_call_block)
            elif item_type == "code_execution_result":
                # Map outcome to status: OUTCOME_OK (1) → success, else → error
                outcome = item.get("outcome", 1)
                status = "success" if outcome == 1 else "error"
                server_tool_result_block: types.ServerToolResult = {
                    "type": "server_tool_result",
                    "tool_call_id": item.get("tool_call_id", ""),
                    "status": status,  # type: ignore[typeddict-item]
                    "output": item.get("code_execution_result", ""),
                }
                server_tool_result_block["extras"] = {"block_type": item_type}
                # Preserve original outcome in extras
                if outcome is not None:
                    server_tool_result_block["extras"]["outcome"] = outcome
                converted_blocks.append(server_tool_result_block)
            elif item_type == "text":
                converted_blocks.append(cast("types.TextContentBlock", item))
            else:
                # Unknown type, preserve as non-standard
                converted_blocks.append({"type": "non_standard", "value": item})
        else:
            # Non-dict, non-string content
            converted_blocks.append({"type": "non_standard", "value": item})

    grounding_metadata = message.response_metadata.get("grounding_metadata")
    if grounding_metadata:
        citations = translate_grounding_metadata_to_citations(grounding_metadata)

        for block in converted_blocks:
            if block["type"] == "text" and citations:
                # Add citations to text blocks (only the first text block)
                block["annotations"] = cast("list[types.Annotation]", citations)
                break

    # Audio is stored on the message.additional_kwargs
    audio_data = message.additional_kwargs.get("audio")
    if audio_data and isinstance(audio_data, bytes):
        audio_block_kwargs: types.AudioContentBlock = {
            "type": "audio",
            "base64": _bytes_to_b64_str(audio_data),
            "mime_type": "audio/wav",  # Default to WAV for Google GenAI
        }
        converted_blocks.append(audio_block_kwargs)

    # Add any missing tool calls from message.tool_calls field
    content_tool_call_ids = {
        block.get("id")
        for block in converted_blocks
        if isinstance(block, dict) and block.get("type") == "tool_call"
    }
    for tool_call in message.tool_calls:
        id_ = tool_call.get("id")
        if id_ and id_ not in content_tool_call_ids:
            missing_tool_call_block: types.ToolCall = {
                "type": "tool_call",
                "id": id_,
                "name": tool_call["name"],
                "args": tool_call["args"],
            }
            converted_blocks.append(missing_tool_call_block)

    return converted_blocks