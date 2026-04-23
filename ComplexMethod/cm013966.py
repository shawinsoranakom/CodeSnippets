def compute_exception_table(
    instructions: list[Instruction],
) -> list[ExceptionTableEntry]:
    """Compute exception table in list format from instructions with exn_tab_entries"""
    exn_dict: dict[tuple[int, int], tuple[int, int, bool]] = {}
    indexof = get_indexof(instructions)

    for inst in instructions:
        if inst.exn_tab_entry:
            # account for prefixed EXTENDED_ARGS
            start = _get_instruction_front(
                instructions, indexof[inst.exn_tab_entry.start]
            ).offset
            assert start is not None
            # point to the last 2 bytes of the end instruction
            end = (
                cast(int, inst.exn_tab_entry.end.offset)
                + instruction_size(inst.exn_tab_entry.end)
                - 2
            )
            assert end is not None
            target = _get_instruction_front(
                instructions, indexof[inst.exn_tab_entry.target]
            ).offset
            assert target is not None
            key = (start, end)
            val = (target, inst.exn_tab_entry.depth, inst.exn_tab_entry.lasti)
            if key in exn_dict:
                assert exn_dict[key] == val
            exn_dict[key] = val

    # Dynamo may construct nested exception table entries for convenience,
    # but Python expects exception table entries to not overlap.
    # NOTE: below, "keys" refer to old instruction entries' starts and ends,
    # and "entries" refer to the generated exception table entries.

    # Sort keys by increasing start, then decreasing end
    keys_sorted = sorted(exn_dict.keys(), key=lambda t: (t[0], -t[1]))
    # smallest byte that the next exception table entry can start at
    nexti = 0
    # stack of current nested keys
    key_stack: list[tuple[int, int]] = []
    exn_tab: list[ExceptionTableEntry] = []

    def pop() -> None:
        """
        Pop the key_stack and append an exception table entry if possible.
        """
        nonlocal nexti
        if key_stack:
            key = key_stack.pop()
            if nexti <= key[1]:
                exn_tab.append(
                    ExceptionTableEntry(max(key[0], nexti), key[1], *exn_dict[key])
                )
                nexti = key[1] + 2

    for key in keys_sorted:
        # pop keys that are no longer nested over the current key
        while key_stack and key_stack[-1][1] < key[0]:
            pop()
        if key_stack:
            # create an entry covering to the current key, if possible
            assert key_stack[-1][0] <= key[0] <= key[1] <= key_stack[-1][1]
            left = max(nexti, key_stack[-1][0])
            if left < key[0]:
                exn_tab.append(
                    ExceptionTableEntry(left, key[0] - 2, *exn_dict[key_stack[-1]])
                )
            nexti = key[0]
        key_stack.append(key)
    while key_stack:
        pop()
    check_exception_table(exn_tab)
    return exn_tab