def sort_imports(file: str, check_only: bool = True):
    """
    Sort the imports defined in the `_import_structure` of a given init.

    Args:
        file (`str`): The path to the init to check/fix.
        check_only (`bool`, *optional*, defaults to `True`): Whether or not to just check (and not auto-fix) the init.
    """
    with open(file, encoding="utf-8") as f:
        code = f.read()

    # If the file is not a custom init, there is nothing to do.
    if "_import_structure = {" not in code:
        return

    # Blocks of indent level 0
    main_blocks = split_code_in_indented_blocks(
        code, start_prompt="_import_structure = {", end_prompt="if TYPE_CHECKING:"
    )

    # We ignore block 0 (everything until start_prompt) and the last block (everything after end_prompt).
    for block_idx in range(1, len(main_blocks) - 1):
        # Check if the block contains some `_import_structure`s thingy to sort.
        block = main_blocks[block_idx]
        block_lines = block.split("\n")

        # Get to the start of the imports.
        line_idx = 0
        while line_idx < len(block_lines) and "_import_structure" not in block_lines[line_idx]:
            # Skip dummy import blocks
            if "import dummy" in block_lines[line_idx]:
                line_idx = len(block_lines)
            else:
                line_idx += 1
        if line_idx >= len(block_lines):
            continue

        # Ignore beginning and last line: they don't contain anything.
        internal_block_code = "\n".join(block_lines[line_idx:-1])
        indent = get_indent(block_lines[1])
        # Slit the internal block into blocks of indent level 1.
        internal_blocks = split_code_in_indented_blocks(internal_block_code, indent_level=indent)
        # We have two categories of import key: list or _import_structure[key].append/extend
        pattern = _re_direct_key if "_import_structure = {" in block_lines[0] else _re_indirect_key
        # Grab the keys, but there is a trap: some lines are empty or just comments.
        keys = [(pattern.search(b).groups()[0] if pattern.search(b) is not None else None) for b in internal_blocks]
        # We only sort the lines with a key.
        keys_to_sort = [(i, key) for i, key in enumerate(keys) if key is not None]
        sorted_indices = [x[0] for x in sorted(keys_to_sort, key=lambda x: x[1])]

        # We reorder the blocks by leaving empty lines/comments as they were and reorder the rest.
        count = 0
        reorderded_blocks = []
        for i in range(len(internal_blocks)):
            if keys[i] is None:
                reorderded_blocks.append(internal_blocks[i])
            else:
                block = sort_objects_in_import(internal_blocks[sorted_indices[count]])
                reorderded_blocks.append(block)
                count += 1

        # And we put our main block back together with its first and last line.
        main_blocks[block_idx] = "\n".join(block_lines[:line_idx] + reorderded_blocks + [block_lines[-1]])

    if code != "\n".join(main_blocks):
        if check_only:
            return True
        else:
            print(f"Overwriting {file}.")
            with open(file, "w", encoding="utf-8") as f:
                f.write("\n".join(main_blocks))