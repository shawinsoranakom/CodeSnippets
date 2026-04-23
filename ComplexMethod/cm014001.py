def remove_dead_code(instructions: list["Instruction"]) -> list["Instruction"]:
    """Dead code elimination"""
    indexof = get_indexof(instructions)
    live_code = set()

    def find_live_code(start: int) -> None:
        for i in range(start, len(instructions)):
            if i in live_code:
                return
            live_code.add(i)
            inst = instructions[i]
            if inst.exn_tab_entry:
                find_live_code(indexof[inst.exn_tab_entry.target])
            if inst.opcode in JUMP_OPCODES:
                assert inst.target is not None
                find_live_code(indexof[inst.target])
            if inst.opcode in TERMINAL_OPCODES:
                return

    find_live_code(0)

    # change exception table entries if start/end instructions are dead
    # assumes that exception table entries have been propagated,
    # e.g. with bytecode_transformation.propagate_inst_exn_table_entries,
    # and that instructions with an exn_tab_entry lies within its start/end.
    if sys.version_info >= (3, 11):
        live_idx = sorted(live_code)
        for i, inst in enumerate(instructions):
            if i in live_code and inst.exn_tab_entry:
                # find leftmost live instruction >= start
                start_idx = bisect.bisect_left(
                    live_idx, indexof[inst.exn_tab_entry.start]
                )
                assert start_idx < len(live_idx)
                # find rightmost live instruction <= end
                end_idx = (
                    bisect.bisect_right(live_idx, indexof[inst.exn_tab_entry.end]) - 1
                )
                assert end_idx >= 0
                assert live_idx[start_idx] <= i <= live_idx[end_idx]
                inst.exn_tab_entry.start = instructions[live_idx[start_idx]]
                inst.exn_tab_entry.end = instructions[live_idx[end_idx]]

    return [inst for i, inst in enumerate(instructions) if i in live_code]