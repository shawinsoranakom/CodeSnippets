def split_code_in_indented_blocks(
    code: str, indent_level: str = "", start_prompt: str | None = None, end_prompt: str | None = None
) -> list[str]:
    """
    Split some code into its indented blocks, starting at a given level.

    Args:
        code (`str`): The code to split.
        indent_level (`str`): The indent level (as string) to use for identifying the blocks to split.
        start_prompt (`str`, *optional*): If provided, only starts splitting at the line where this text is.
        end_prompt (`str`, *optional*): If provided, stops splitting at a line where this text is.

    Warning:
        The text before `start_prompt` or after `end_prompt` (if provided) is not ignored, just not split. The input `code`
        can thus be retrieved by joining the result.

    Returns:
        `List[str]`: The list of blocks.
    """
    # Let's split the code into lines and move to start_index.
    index = 0
    lines = code.split("\n")
    if start_prompt is not None:
        while not lines[index].startswith(start_prompt):
            index += 1
        blocks = ["\n".join(lines[:index])]
    else:
        blocks = []

    # This variable contains the block treated at a given time.
    current_block = [lines[index]]
    index += 1
    # We split into blocks until we get to the `end_prompt` (or the end of the file).
    while index < len(lines) and (end_prompt is None or not lines[index].startswith(end_prompt)):
        # We have a non-empty line with the proper indent -> start of a new block
        if len(lines[index]) > 0 and get_indent(lines[index]) == indent_level:
            # Store the current block in the result and rest. There are two cases: the line is part of the block (like
            # a closing parenthesis) or not.
            if len(current_block) > 0 and get_indent(current_block[-1]).startswith(indent_level + " "):
                # Line is part of the current block
                current_block.append(lines[index])
                blocks.append("\n".join(current_block))
                if index < len(lines) - 1:
                    current_block = [lines[index + 1]]
                    index += 1
                else:
                    current_block = []
            else:
                # Line is not part of the current block
                blocks.append("\n".join(current_block))
                current_block = [lines[index]]
        else:
            # Just add the line to the current block
            current_block.append(lines[index])
        index += 1

    # Adds current block if it's nonempty.
    if len(current_block) > 0:
        blocks.append("\n".join(current_block))

    # Add final block after end_prompt if provided.
    if end_prompt is not None and index < len(lines):
        blocks.append("\n".join(lines[index:]))

    return blocks