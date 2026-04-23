def devirtualize_jumps(instructions: list[Instruction]) -> None:
    """Fill in args for virtualized jump target after instructions may have moved"""
    jumps = set(dis.hasjabs).union(set(dis.hasjrel))

    # check for negative jump args and fix them
    for inst in instructions:
        if inst.opcode in jumps:
            if inst.opcode not in dis.hasjabs:
                assert (
                    inst.target is not None
                    and inst.target.offset is not None
                    and inst.offset is not None
                )
                if inst.target.offset < inst.offset:
                    if sys.version_info < (3, 11):
                        raise RuntimeError("Got negative jump offset for Python < 3.11")
                    # forward jumps become backward
                    if "FORWARD" in inst.opname:
                        flip_jump_direction(inst)
                else:
                    # backward jumps become forward
                    if sys.version_info >= (3, 11) and "BACKWARD" in inst.opname:
                        flip_jump_direction(inst)

    # jump instruction size may have changed due to flips
    update_offsets(instructions)
    indexof = get_indexof(instructions)

    # compute jump instruction arg
    for inst in instructions:
        if inst.opcode in jumps:
            assert inst.target is not None
            target = _get_instruction_front(instructions, indexof[inst.target])
            if inst.opcode in dis.hasjabs:
                if sys.version_info < (3, 11):
                    # `arg` is expected to be bytecode offset, whereas `offset` is byte offset.
                    # Divide since bytecode is 2 bytes large.
                    assert target.offset is not None
                    inst.arg = int(target.offset / 2)
                else:
                    raise RuntimeError("Python 3.11+ should not have absolute jumps")
            else:  # relative jump
                # byte offset between target and next instruction
                assert target.offset is not None and inst.offset is not None
                inst.arg = abs(
                    int(target.offset - inst.offset - instruction_size(inst))
                )
                # pyrefly: ignore [unsupported-operation]
                inst.arg //= 2
            inst.argval = target.offset
            inst.argrepr = f"to {target.offset}"