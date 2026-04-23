def get_instruction_size_for_uop(instructions: dict[str, Instruction], uop: Uop) -> int | None:
    """Return the size of the instruction that contains the given uop or
    `None` if the uop does not contains the `INSTRUCTION_SIZE` macro.

    If there is more than one instruction that contains the uop,
    ensure that they all have the same size.
    """
    for tkn in uop.body.tokens():
        if tkn.text == "INSTRUCTION_SIZE":
            break
    else:
        return None

    size = None
    for inst in instructions.values():
        if uop in inst.parts:
            if size is None:
                size = inst.size
            if size != inst.size:
                raise analysis_error(
                    "All instructions containing a uop with the `INSTRUCTION_SIZE` macro "
                    f"must have the same size: {size} != {inst.size}",
                    tkn
                )
    if size is None:
        raise analysis_error(f"No instruction containing the uop '{uop.name}' was found", tkn)
    return size