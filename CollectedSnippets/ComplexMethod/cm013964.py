def assemble(instructions: list[Instruction], firstlineno: int) -> tuple[bytes, bytes]:
    """Do the opposite of dis.get_instructions()"""
    code: list[int] = []
    if sys.version_info >= (3, 11):
        lnotab, update_lineno = linetable_311_writer(firstlineno)
        num_ext = 0
        for i, inst in enumerate(instructions):
            if inst.opname == "EXTENDED_ARG":
                inst_size = 1
                num_ext += 1
                # copy positions from the actual instruction
                for j in (1, 2, 3):
                    if instructions[i + j].opname != "EXTENDED_ARG":
                        inst.positions = instructions[i + j].positions
                        break
            else:
                inst_size = instruction_size(inst) // 2 + num_ext
                num_ext = 0
            update_lineno(inst.positions, inst_size)
            num_ext = 0
            arg = inst.arg or 0
            code.extend((inst.opcode, arg & 0xFF))
            for _ in range(instruction_size(inst) // 2 - 1):
                code.extend((0, 0))
    else:
        lnotab, update_lineno, end = linetable_writer(firstlineno)

        for inst in instructions:
            if inst.starts_line is not None:
                update_lineno(inst.starts_line, len(code))
            arg = inst.arg or 0
            code.extend((inst.opcode, arg & 0xFF))

        end(len(code))

    return bytes(code), bytes(lnotab)