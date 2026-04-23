def _convert_file_block_to_openrouter(block: dict[str, Any]) -> dict[str, Any]:
    """Convert a LangChain file content block to OpenRouter's `file` format.

    OpenRouter accepts files as::

        {"type": "file", "file": {"filename": "...", "file_data": "..."}}

    where `file_data` is either a public URL or a `data:` URI.

    Args:
        block: A LangChain file content block.

    Returns:
        A dict in OpenRouter's `file` format.

    Raises:
        ValueError: If the block contains neither a URL, base64 data, nor a
            file ID.
    """
    file: dict[str, str] = {}

    # --- resolve file_data ---------------------------------------------------
    if "url" in block:
        file["file_data"] = block["url"]
    elif block.get("source_type") == "base64" or "base64" in block:
        base64_data = block["data"] if "source_type" in block else block["base64"]
        mime_type = block.get("mime_type", "application/octet-stream")
        file["file_data"] = f"data:{mime_type};base64,{base64_data}"
    elif block.get("source_type") == "id" or "file_id" in block:
        msg = "OpenRouter does not support file IDs."
        raise ValueError(msg)
    else:
        msg = "File block must have either 'url' or 'base64' data."
        raise ValueError(msg)

    # --- resolve filename ----------------------------------------------------
    if filename := block.get("filename"):
        file["filename"] = filename
    elif ((extras := block.get("extras")) and "filename" in extras) or (
        (extras := block.get("metadata")) and "filename" in extras
    ):
        file["filename"] = extras["filename"]

    return {"type": "file", "file": file}