def _format_content_block_xml(block: dict) -> str | None:
    """Format a content block as XML.

    Args:
        block: A LangChain content block.

    Returns:
        XML string representation of the block, or `None` if the block should be
            skipped.

    Note:
        Plain text document content, server tool call arguments, and server tool
        result outputs are truncated to 500 characters.
    """
    block_type = block.get("type", "")

    # Skip blocks with base64 encoded data
    if _has_base64_data(block):
        return None

    # Text blocks
    if block_type == "text":
        text = block.get("text", "")
        return escape(text) if text else None

    # Reasoning blocks
    if block_type == "reasoning":
        reasoning = block.get("reasoning", "")
        if reasoning:
            return f"<reasoning>{escape(reasoning)}</reasoning>"
        return None

    # Image blocks (URL only, base64 already filtered)
    if block_type == "image":
        url = block.get("url")
        file_id = block.get("file_id")
        if url:
            return f"<image url={quoteattr(url)} />"
        if file_id:
            return f"<image file_id={quoteattr(file_id)} />"
        return None

    # OpenAI-style image_url blocks
    if block_type == "image_url":
        image_url = block.get("image_url", {})
        if isinstance(image_url, dict):
            url = image_url.get("url", "")
            if url and not url.startswith("data:"):
                return f"<image url={quoteattr(url)} />"
        return None

    # Audio blocks (URL only)
    if block_type == "audio":
        url = block.get("url")
        file_id = block.get("file_id")
        if url:
            return f"<audio url={quoteattr(url)} />"
        if file_id:
            return f"<audio file_id={quoteattr(file_id)} />"
        return None

    # Video blocks (URL only)
    if block_type == "video":
        url = block.get("url")
        file_id = block.get("file_id")
        if url:
            return f"<video url={quoteattr(url)} />"
        if file_id:
            return f"<video file_id={quoteattr(file_id)} />"
        return None

    # Plain text document blocks
    if block_type == "text-plain":
        text = block.get("text", "")
        return escape(_truncate(text)) if text else None

    # Server tool call blocks (from AI messages)
    if block_type == "server_tool_call":
        tc_id = quoteattr(str(block.get("id") or ""))
        tc_name = quoteattr(str(block.get("name") or ""))
        tc_args_json = json.dumps(block.get("args", {}), ensure_ascii=False)
        tc_args = escape(_truncate(tc_args_json))
        return (
            f"<server_tool_call id={tc_id} name={tc_name}>{tc_args}</server_tool_call>"
        )

    # Server tool result blocks
    if block_type == "server_tool_result":
        tool_call_id = quoteattr(str(block.get("tool_call_id") or ""))
        status = quoteattr(str(block.get("status") or ""))
        output = block.get("output")
        if output:
            output_json = json.dumps(output, ensure_ascii=False)
            output_str = escape(_truncate(output_json))
        else:
            output_str = ""
        return (
            f"<server_tool_result tool_call_id={tool_call_id} status={status}>"
            f"{output_str}</server_tool_result>"
        )

    # Unknown block type - skip silently
    return None