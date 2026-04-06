def replace_multiline_code_blocks_in_text(
    text: list[str],
    code_blocks: list[MultilineCodeBlockInfo],
    original_code_blocks: list[MultilineCodeBlockInfo],
) -> list[str]:
    """
    Update each code block in `text` with the corresponding code block from
    `original_code_blocks` with comments taken from `code_blocks`.

    Raises ValueError if the number, language, or shape of code blocks do not match.
    """

    if len(code_blocks) != len(original_code_blocks):
        raise ValueError(
            "Number of code blocks does not match the number in the original document "
            f"({len(code_blocks)} vs {len(original_code_blocks)})"
        )

    modified_text = text.copy()
    for block, original_block in zip(code_blocks, original_code_blocks, strict=True):
        updated_content = replace_multiline_code_block(block, original_block)

        start_line_index = block["start_line_no"] - 1
        for i, updated_line in enumerate(updated_content):
            modified_text[start_line_index + i] = updated_line

    return modified_text