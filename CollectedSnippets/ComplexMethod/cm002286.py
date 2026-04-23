def split_code_into_blocks(
    lines: list[str], start_index: int, end_index: int, indent: int, backtrace: bool = False
) -> list[tuple[str, int, int]]:
    """
    Split the class/func block starting at `start_index` in a source code (defined by `lines`) into *inner blocks*.

    The block's header is included as the first element. The contiguous regions (without empty lines) that are not
    inside any inner block are included as blocks. The contiguous regions of empty lines that are not inside any inner
    block are also included as (dummy) blocks.

    Args:
        lines (`List[str]`):
            The source code, represented by a list of lines.
        start_index (`int`):
            The starting index of the target class/func block.
        end_index (`int`):
            The ending index of the target class/func block.
        indent (`int`):
            The indent of the class/func body.
        backtrace (`bool`, *optional*, defaults to `False`):
            Whether or not to include the lines before the inner class/func block's header (e.g. comments, decorators,
            etc.) until an empty line is encountered.

    Returns:
        `List[Tuple[str, int, int]]`: A list of elements with the form `(block_name, start_index, end_index)`.
    """
    splits = []
    # `indent - 4` is the indent level of the target class/func header
    try:
        target_block_name = re.search(
            rf"^{' ' * (indent - 4)}((class|def)\s+\S+)(\(|\:)", lines[start_index]
        ).groups()[0]
    except Exception:
        start_context = min(start_index - 10, 0)
        end_context = min(end_index + 10, len(lines))
        raise ValueError(
            f"Tried to split a class or function. It did not work. Error comes from line {start_index}: \n```\n"
            + "".join(lines[start_context:end_context])
            + "```\n"
        )

    # from now on, the `block` means inner blocks unless explicitly specified
    indent_str = " " * indent
    block_without_name_idx = 0
    empty_block_idx = 0

    # Find the lines for the definition header
    index = start_index
    if "(" in lines[start_index] and "):" not in lines[start_index] in lines[start_index]:
        while index < end_index:
            if _is_definition_header_ending_line(lines[index]):
                break
            index += 1

    # the first line outside the definition header
    index += 1
    splits.append((target_block_name, start_index, index))

    block_start_index, prev_block_end_index = index, index
    while index < end_index:
        # if found, it will be an inner block
        block_found = re.search(rf"^{indent_str}((class|def)\s+\S+)(\(|\:)", lines[index])
        if block_found:
            name = block_found.groups()[0]

            block_end_index = find_block_end(lines, index, indent + 4)

            # backtrace to include the lines before the found block's definition header (e.g. comments, decorators,
            # etc.) until an empty line is encountered.
            block_start_index = index
            if index > prev_block_end_index and backtrace:
                idx = index - 1
                for idx in range(index - 1, prev_block_end_index - 2, -1):
                    if not (len(lines[idx].strip()) > 0 and lines[idx].startswith(indent_str)):
                        break
                idx += 1
                if idx < index:
                    block_start_index = idx

            # between the current found block and the previous found block
            if block_start_index > prev_block_end_index:
                # give it a dummy name
                if len("".join(lines[prev_block_end_index:block_start_index]).strip()) == 0:
                    prev_block_name = f"_empty_block_{empty_block_idx}"
                    empty_block_idx += 1
                else:
                    prev_block_name = f"_block_without_name_{block_without_name_idx}"
                    block_without_name_idx += 1
                # Add it as a block
                splits.append((prev_block_name, prev_block_end_index, block_start_index))

            # Add the current found block
            splits.append((name, block_start_index, block_end_index))
            prev_block_end_index = block_end_index
            index = block_end_index - 1

        index += 1

    if index > prev_block_end_index:
        if len("".join(lines[prev_block_end_index:index]).strip()) == 0:
            prev_block_name = f"_empty_block_{empty_block_idx}"
        else:
            prev_block_name = f"_block_without_name_{block_without_name_idx}"
        splits.append((prev_block_name, prev_block_end_index, index))

    return splits