def _flatten_tool_result_content(blocks: list) -> str:
    """Flatten tool_result and other content blocks into plain text.

    Handles nested tool_result structures, text blocks, and raw strings.
    Uses ``json.dumps`` as fallback for dict blocks without a ``text`` key
    or where ``text`` is ``None``.

    Like ``_flatten_assistant_content``, structured blocks (images, nested
    tool results) are reduced to text representations for compression.
    """
    str_parts: list[str] = []
    for block in blocks:
        if isinstance(block, dict) and block.get("type") == "tool_result":
            inner = block.get("content") or ""
            if isinstance(inner, list):
                for sub in inner:
                    if isinstance(sub, dict):
                        sub_type = sub.get("type")
                        if sub_type in ("image", "document"):
                            # Avoid serializing base64 binary data into
                            # the compaction input — use a placeholder.
                            str_parts.append(f"[__{sub_type}__]")
                        elif sub_type == "text" or sub.get("text") is not None:
                            str_parts.append(str(sub.get("text", "")))
                        else:
                            str_parts.append(json.dumps(sub))
                    else:
                        str_parts.append(str(sub))
            else:
                str_parts.append(str(inner))
        elif isinstance(block, dict) and block.get("type") == "text":
            str_parts.append(str(block.get("text", "")))
        elif isinstance(block, dict):
            # Preserve non-text/non-tool_result blocks (e.g. image) as placeholders.
            # Use __prefix__ to distinguish from literal user text.
            btype = block.get("type", "unknown")
            str_parts.append(f"[__{btype}__]")
        elif isinstance(block, str):
            str_parts.append(block)
    return "\n".join(str_parts) if str_parts else ""