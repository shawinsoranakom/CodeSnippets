def stacksize_analysis(instructions: list["Instruction"]) -> int | float:
    assert instructions
    fixed_point = FixedPointBox()
    stack_sizes = {
        inst: StackSize(float("inf"), float("-inf"), fixed_point)
        for inst in instructions
    }
    stack_sizes[instructions[0]].zero()

    for _ in range(100):
        if fixed_point.value:
            break
        fixed_point.value = True

        for inst, next_inst in zip(instructions, instructions[1:] + [None]):
            stack_size = stack_sizes[inst]
            if inst.opcode not in TERMINAL_OPCODES:
                assert next_inst is not None, f"missing next inst: {inst}"
                eff = stack_effect(inst.opcode, inst.arg, jump=False)
                stack_sizes[next_inst].offset_of(stack_size, eff)
            if inst.opcode in JUMP_OPCODES:
                assert inst.target is not None, f"missing target: {inst}"
                stack_sizes[inst.target].offset_of(
                    stack_size, stack_effect(inst.opcode, inst.arg, jump=True)
                )
            if inst.exn_tab_entry:
                # see https://github.com/python/cpython/blob/3.11/Objects/exception_handling_notes.txt
                # on why depth is computed this way.
                depth = inst.exn_tab_entry.depth + int(inst.exn_tab_entry.lasti) + 1
                stack_sizes[inst.exn_tab_entry.target].exn_tab_jump(depth)

    low = min(x.low for x in stack_sizes.values())
    high = max(x.high for x in stack_sizes.values())

    assert fixed_point.value, "failed to reach fixed point"
    assert low >= 0
    return high