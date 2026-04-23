def add_push_null(
    inst_or_insts: Instruction | list[Instruction],
) -> list[Instruction]:
    """
    Appends or prepends a PUSH_NULL instruction to `inst_or_insts`,
    depending on Python version. Used when you know that
    `inst_or_insts` generates a callable that will be called.

    NOTE: Assumes `inst_or_insts` is a single instruction or sequence of
    instructions that pushes exactly 1 object to the stack that is to
    be called. It is important that you include ALL instructions that
    construct the callable - not just the first instruction/a prefix.

    Will attempt to use the NULL push bit for instructions
    with such bits (LOAD_GLOBAL 3.11+, LOAD_ATTR 3.12+, LOAD_SUPER_ATTR).
    In this case, instructions WILL be modified.
    """
    if isinstance(inst_or_insts, Instruction):
        insts: list[Instruction] = [inst_or_insts]
    else:
        assert isinstance(inst_or_insts, list)
        insts = inst_or_insts

    def inst_has_bit_set(idx: int) -> bool:
        assert insts[idx].arg is not None
        return insts[idx].arg & 1 == 1  # type: ignore[operator]

    def set_inst_bit(idx: int) -> None:
        assert insts[idx].arg is not None
        insts[idx].arg |= 1  # type: ignore[operator]

    if sys.version_info >= (3, 13):
        # In 3.13, NULL follows the callable
        if inst_has_op_bits(insts[-1].opname) and not inst_has_bit_set(-1):
            # All insts with op bits have the push_null bit as the last one.
            # Only set the bit if it hasn't been set - otherwise, we need
            # to add another PUSH_NULL.
            set_inst_bit(-1)
        else:
            insts = insts + [create_instruction("PUSH_NULL")]
    elif sys.version_info >= (3, 12):
        # LOAD_ATTR/LOAD_SUPER_ATTR at the end
        # We assume that `insts` will only load 1 object, so
        # LOAD_GLOBAL at the end doesn't need to be checked
        if inst_has_op_bits(insts[-1].opname) and not inst_has_bit_set(-1):
            set_inst_bit(-1)
        elif insts[0].opname == "LOAD_GLOBAL" and not inst_has_bit_set(0):
            set_inst_bit(0)
        else:
            insts = [create_instruction("PUSH_NULL")] + insts
    elif sys.version_info >= (3, 11):
        # 3.11 introduced NULL preceding callable
        if inst_has_op_bits(insts[0].opname) and not inst_has_bit_set(0):
            set_inst_bit(0)
        else:
            insts = [create_instruction("PUSH_NULL")] + insts
    return insts