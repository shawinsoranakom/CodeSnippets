def _extract_output_text(output: str | list) -> str:
    if isinstance(output, str):
        return output
    if isinstance(output, list) and len(output) == 0:
        return ""

    # Handle lists of various lengths and formats
    if isinstance(output, list):
        # Handle single item lists
        if len(output) == 1:
            item = output[0]
            if isinstance(item, str):
                return item
            if isinstance(item, dict):
                if "text" in item:
                    return item["text"] or ""
                if "content" in item:
                    return str(item["content"])
                if "message" in item:
                    return str(item["message"])

                # Special case handling for non-text-like dicts
                if (
                    item.get("type") == "tool_use"  # Handle tool use items
                    or ("index" in item and len(item) == 1)  # Handle index-only items
                    or "partial_json" in item  # Handle partial json items
                    # Handle index-only items
                    or ("index" in item and not any(k in item for k in ("text", "content", "message")))
                    # Handle other metadata-only chunks that don't contain meaningful text
                    or not any(key in item for key in ["text", "content", "message"])
                ):
                    return ""

                # For any other dict format, return empty string
                return ""
            # For any other single item type (not str or dict), return empty string
            return ""

        # Handle multiple items - extract text from all text-type items
        text_parts = []
        for item in output:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict):
                if "text" in item and item["text"] is not None:
                    text_parts.append(item["text"])
                # Skip tool_use, index-only, and partial_json items
                elif item.get("type") == "tool_use" or "partial_json" in item or ("index" in item and len(item) == 1):
                    continue
        return "".join(text_parts)

    # If we get here, the format is unexpected but try to be graceful
    return ""