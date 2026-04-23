def merge_content(
    first_content: str | list[str | dict],
    *contents: str | list[str | dict],
) -> str | list[str | dict]:
    """Merge multiple message contents.

    Args:
        first_content: The first `content`. Can be a string or a list.
        contents: The other `content`s. Can be a string or a list.

    Returns:
        The merged content.

    """
    merged: str | list[str | dict]
    merged = "" if first_content is None else first_content

    for content in contents:
        # If current is a string
        if isinstance(merged, str):
            # If the next chunk is also a string, then merge them naively
            if isinstance(content, str):
                merged += content
            # If the next chunk is a list, add the current to the start of the list
            else:
                merged = [merged, *content]
        elif isinstance(content, list):
            # If both are lists
            merged = merge_lists(cast("list", merged), content)  # type: ignore[assignment]
        # If the first content is a list, and the second content is a string
        # If the last element of the first content is a string
        # Add the second content to the last element
        elif merged and isinstance(merged[-1], str):
            merged[-1] += content
        # If second content is an empty string, treat as a no-op
        elif content == "":
            pass
        # Otherwise, add the second content as a new element of the list
        elif merged:
            merged.append(content)
    return merged