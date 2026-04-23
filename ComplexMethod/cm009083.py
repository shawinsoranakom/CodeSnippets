def _format_message_content(
    content: Any,
    api: Literal["chat/completions", "responses"] = "chat/completions",
    role: str | None = None,
) -> Any:
    """Format message content."""
    if content and isinstance(content, list):
        formatted_content = []
        for block in content:
            # Remove unexpected block types
            if (
                isinstance(block, dict)
                and "type" in block
                and (
                    block["type"] in ("tool_use", "thinking", "reasoning_content")
                    or (
                        block["type"] in ("function_call", "code_interpreter_call")
                        and api == "chat/completions"
                    )
                )
            ):
                continue
            if (
                isinstance(block, dict)
                and is_data_content_block(block)
                # Responses API messages handled separately in _compat (parsed into
                # image generation calls)
                and not (api == "responses" and str(role).lower().startswith("ai"))
            ):
                formatted_content.append(convert_to_openai_data_block(block, api=api))
            # Anthropic image blocks
            elif (
                isinstance(block, dict)
                and block.get("type") == "image"
                and (source := block.get("source"))
                and isinstance(source, dict)
            ):
                if source.get("type") == "base64" and (
                    (media_type := source.get("media_type"))
                    and (data := source.get("data"))
                ):
                    formatted_content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{media_type};base64,{data}"},
                        }
                    )
                elif source.get("type") == "url" and (url := source.get("url")):
                    formatted_content.append(
                        {"type": "image_url", "image_url": {"url": url}}
                    )
                else:
                    continue
            else:
                formatted_content.append(block)
    else:
        formatted_content = content

    return formatted_content