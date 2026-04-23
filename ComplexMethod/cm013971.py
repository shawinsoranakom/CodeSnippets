def fix_extended_args(instructions: list[Instruction]) -> int:
    """Fill in correct argvals for EXTENDED_ARG ops"""
    output: list[Instruction] = []

    def maybe_pop_n(n: int) -> None:
        for _ in range(n):
            if output and output[-1].opcode == dis.EXTENDED_ARG:
                output.pop()

    for inst in instructions:
        if inst.opcode == dis.EXTENDED_ARG:
            # Leave this instruction alone for now so we never shrink code
            inst.arg = 0
        elif inst.arg and inst.arg > 0xFFFFFF:
            maybe_pop_n(3)
            output.append(create_instruction("EXTENDED_ARG", arg=inst.arg >> 24))
            output.append(create_instruction("EXTENDED_ARG", arg=inst.arg >> 16))
            output.append(create_instruction("EXTENDED_ARG", arg=inst.arg >> 8))
        elif inst.arg and inst.arg > 0xFFFF:
            maybe_pop_n(2)
            output.append(create_instruction("EXTENDED_ARG", arg=inst.arg >> 16))
            output.append(create_instruction("EXTENDED_ARG", arg=inst.arg >> 8))
        elif inst.arg and inst.arg > 0xFF:
            maybe_pop_n(1)
            output.append(create_instruction("EXTENDED_ARG", arg=inst.arg >> 8))
        output.append(inst)

    added = len(output) - len(instructions)
    assert added >= 0
    instructions[:] = output
    return added