def _content_blocks_equal_ignore_id(
    actual: str | list[Any], expected: str | list[Any]
) -> bool:
    """Compare content blocks, ignoring auto-generated `id` fields.

    Args:
        actual: Actual content from response (string or list of content blocks).
        expected: Expected content to compare against (string or list of blocks).

    Returns:
        True if content matches (excluding `id` fields), `False` otherwise.

    """
    if isinstance(actual, str) or isinstance(expected, str):
        return actual == expected

    if len(actual) != len(expected):
        return False
    for actual_block, expected_block in zip(actual, expected, strict=False):
        actual_without_id = (
            {k: v for k, v in actual_block.items() if k != "id"}
            if isinstance(actual_block, dict) and "id" in actual_block
            else actual_block
        )

        if actual_without_id != expected_block:
            return False

    return True