def _convert_mcp_result(result: Any) -> Any:
    """Convert a CallToolResult into a format LangChain agents can consume.

    - Text-only results → plain string (backward compatible).
    - Results containing images or unsupported blocks → list of LangChain
      content blocks so that vision-capable LLMs receive proper multimodal
      input instead of a raw base64 string (fixes issue #11812).
    - Unsupported block types (resource, resource_link, audio, etc.) are
      serialised as ``{"type": "text", "text": json.dumps(block)}`` so no
      content is silently dropped on the agent path.
    - Only collapses back to a plain string when every block is plain text.
    """
    if result is None:
        return ""

    content = getattr(result, "content", None)
    if not content:
        return ""

    needs_list = any(getattr(block, "type", None) != "text" for block in content)

    if not needs_list:
        # Text-only: join all text blocks into a single string (backward compat)
        return "\n".join(getattr(block, "text", "") for block in content if getattr(block, "type", None) == "text")

    # Mixed or non-text: build a list of LangChain content blocks
    blocks: list[dict] = []
    for block in content:
        block_type = getattr(block, "type", None)
        if block_type == "text":
            blocks.append({"type": "text", "text": getattr(block, "text", "")})
        elif block_type == "image":
            mime = getattr(block, "mimeType", None) or "image/png"
            data = getattr(block, "data", "")
            blocks.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{data}"},
                }
            )
        else:
            # Unsupported block type (resource, resource_link, audio, …):
            # serialise to JSON text so no content is lost on the agent path.
            try:
                raw_text = json.dumps(block.model_dump(), ensure_ascii=False)
            except AttributeError:
                raw_text = json.dumps({"type": block_type, "raw": str(block)}, ensure_ascii=False)
            blocks.append({"type": "text", "text": raw_text})
    return blocks