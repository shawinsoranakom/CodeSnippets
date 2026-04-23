def _format_data_content_block(block: dict) -> dict:
    """Format standard data content block to format expected by Anthropic."""
    if block["type"] == "image":
        if "url" in block:
            if block["url"].startswith("data:"):
                # Data URI
                formatted_block = {
                    "type": "image",
                    "source": _format_image(block["url"]),
                }
            else:
                formatted_block = {
                    "type": "image",
                    "source": {"type": "url", "url": block["url"]},
                }
        elif "base64" in block or block.get("source_type") == "base64":
            formatted_block = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": block["mime_type"],
                    "data": block.get("base64") or block.get("data", ""),
                },
            }
        elif "file_id" in block:
            formatted_block = {
                "type": "image",
                "source": {
                    "type": "file",
                    "file_id": block["file_id"],
                },
            }
        elif block.get("source_type") == "id":
            formatted_block = {
                "type": "image",
                "source": {
                    "type": "file",
                    "file_id": block["id"],
                },
            }
        else:
            msg = (
                "Anthropic only supports 'url', 'base64', or 'id' keys for image "
                "content blocks."
            )
            raise ValueError(
                msg,
            )

    elif block["type"] == "file":
        if "url" in block:
            formatted_block = {
                "type": "document",
                "source": {
                    "type": "url",
                    "url": block["url"],
                },
            }
        elif "base64" in block or block.get("source_type") == "base64":
            formatted_block = {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": block.get("mime_type") or "application/pdf",
                    "data": block.get("base64") or block.get("data", ""),
                },
            }
        elif block.get("source_type") == "text":
            formatted_block = {
                "type": "document",
                "source": {
                    "type": "text",
                    "media_type": block.get("mime_type") or "text/plain",
                    "data": block["text"],
                },
            }
        elif "file_id" in block:
            formatted_block = {
                "type": "document",
                "source": {
                    "type": "file",
                    "file_id": block["file_id"],
                },
            }
        elif block.get("source_type") == "id":
            formatted_block = {
                "type": "document",
                "source": {
                    "type": "file",
                    "file_id": block["id"],
                },
            }
        else:
            msg = (
                "Anthropic only supports 'url', 'base64', or 'id' keys for file "
                "content blocks."
            )
            raise ValueError(msg)

    elif block["type"] == "text-plain":
        formatted_block = {
            "type": "document",
            "source": {
                "type": "text",
                "media_type": block.get("mime_type") or "text/plain",
                "data": block["text"],
            },
        }

    else:
        msg = f"Block of type {block['type']} is not supported."
        raise ValueError(msg)

    if formatted_block:
        for key in ["cache_control", "citations", "title", "context"]:
            if key in block:
                formatted_block[key] = block[key]
            elif (metadata := block.get("extras")) and key in metadata:
                formatted_block[key] = metadata[key]
            elif (metadata := block.get("metadata")) and key in metadata:
                # Backward compat
                formatted_block[key] = metadata[key]

    return formatted_block