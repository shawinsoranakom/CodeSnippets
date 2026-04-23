def _iter_blocks() -> Iterator[types.ContentBlock]:
        blocks: list[dict[str, Any]] = [
            cast("dict[str, Any]", block)
            if block.get("type") != "non_standard"
            else block["value"]  # type: ignore[typeddict-item]  # this is only non-standard blocks
            for block in content
        ]
        for block in blocks:
            num_keys = len(block)
            block_type = block.get("type")

            if num_keys == 1 and (text := block.get("text")):
                # This is probably a TextContentBlock
                yield {"type": "text", "text": text}

            elif (
                num_keys == 1
                and (document := block.get("document"))
                and isinstance(document, dict)
                and "format" in document
            ):
                # Handle document format conversion
                doc_format = document.get("format")
                source = document.get("source", {})

                if doc_format == "pdf" and "bytes" in source:
                    # PDF document with byte data
                    file_block: types.FileContentBlock = {
                        "type": "file",
                        "base64": source["bytes"]
                        if isinstance(source["bytes"], str)
                        else _bytes_to_b64_str(source["bytes"]),
                        "mime_type": "application/pdf",
                    }
                    # Preserve extra fields
                    extras = {
                        key: value
                        for key, value in document.items()
                        if key not in {"format", "source"}
                    }
                    if extras:
                        file_block["extras"] = extras
                    yield file_block

                elif doc_format == "txt" and "text" in source:
                    # Text document
                    plain_text_block: types.PlainTextContentBlock = {
                        "type": "text-plain",
                        "text": source["text"],
                        "mime_type": "text/plain",
                    }
                    # Preserve extra fields
                    extras = {
                        key: value
                        for key, value in document.items()
                        if key not in {"format", "source"}
                    }
                    if extras:
                        plain_text_block["extras"] = extras
                    yield plain_text_block

                else:
                    # Unknown document format
                    yield {"type": "non_standard", "value": block}

            elif (
                num_keys == 1
                and (image := block.get("image"))
                and isinstance(image, dict)
                and "format" in image
            ):
                # Handle image format conversion
                img_format = image.get("format")
                source = image.get("source", {})

                if "bytes" in source:
                    # Image with byte data
                    image_block: types.ImageContentBlock = {
                        "type": "image",
                        "base64": source["bytes"]
                        if isinstance(source["bytes"], str)
                        else _bytes_to_b64_str(source["bytes"]),
                        "mime_type": f"image/{img_format}",
                    }
                    # Preserve extra fields
                    extras = {}
                    for key, value in image.items():
                        if key not in {"format", "source"}:
                            extras[key] = value
                    if extras:
                        image_block["extras"] = extras
                    yield image_block

                else:
                    # Image without byte data
                    yield {"type": "non_standard", "value": block}

            elif block_type == "file_data" and "file_uri" in block:
                # Handle FileData URI-based content
                uri_file_block: types.FileContentBlock = {
                    "type": "file",
                    "url": block["file_uri"],
                }
                if mime_type := block.get("mime_type"):
                    uri_file_block["mime_type"] = mime_type
                yield uri_file_block

            elif block_type == "function_call" and "name" in block:
                # Handle function calls
                tool_call_block: types.ToolCall = {
                    "type": "tool_call",
                    "name": block["name"],
                    "args": block.get("args", {}),
                    "id": block.get("id", ""),
                }
                yield tool_call_block

            elif block_type == "executable_code":
                server_tool_call_input: types.ServerToolCall = {
                    "type": "server_tool_call",
                    "name": "code_interpreter",
                    "args": {
                        "code": block.get("executable_code", ""),
                        "language": block.get("language", "python"),
                    },
                    "id": block.get("id", ""),
                }
                yield server_tool_call_input

            elif block_type == "code_execution_result":
                outcome = block.get("outcome", 1)
                status = "success" if outcome == 1 else "error"
                server_tool_result_input: types.ServerToolResult = {
                    "type": "server_tool_result",
                    "tool_call_id": block.get("tool_call_id", ""),
                    "status": status,  # type: ignore[typeddict-item]
                    "output": block.get("code_execution_result", ""),
                }
                if outcome is not None:
                    server_tool_result_input["extras"] = {"outcome": outcome}
                yield server_tool_result_input

            elif block.get("type") in types.KNOWN_BLOCK_TYPES:
                # We see a standard block type, so we just cast it, even if
                # we don't fully understand it. This may be dangerous, but
                # it's better than losing information.
                yield cast("types.ContentBlock", block)

            else:
                # We don't understand this block at all.
                yield {"type": "non_standard", "value": block}