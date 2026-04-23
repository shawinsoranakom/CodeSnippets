def assign_opcodes(
    instructions: dict[str, Instruction],
    families: dict[str, Family],
    pseudos: dict[str, PseudoInstruction],
) -> tuple[dict[str, int], int, int]:
    """Assigns opcodes, then returns the opmap,
    have_arg and min_instrumented values"""
    instmap: dict[str, int] = {}

    # 0 is reserved for cache entries. This helps debugging.
    instmap["CACHE"] = 0

    # 17 is reserved as it is the initial value for the specializing counter.
    # This helps catch cases where we attempt to execute a cache.
    instmap["RESERVED"] = 17

    # 128 is RESUME - it is hard coded as such in Tools/build/deepfreeze.py
    instmap["RESUME"] = 128

    # This is an historical oddity.
    instmap["BINARY_OP_INPLACE_ADD_UNICODE"] = 3

    instmap["INSTRUMENTED_LINE"] = 253
    instmap["ENTER_EXECUTOR"] = 254
    instmap["TRACE_RECORD"] = 255

    instrumented = [name for name in instructions if name.startswith("INSTRUMENTED")]

    specialized: set[str] = set()
    no_arg: list[str] = []
    has_arg: list[str] = []

    for family in families.values():
        specialized.update(inst.name for inst in family.members)

    for inst in instructions.values():
        name = inst.name
        if name in specialized:
            continue
        if name in instrumented:
            continue
        if inst.properties.oparg:
            has_arg.append(name)
        else:
            no_arg.append(name)

    # Specialized ops appear in their own section
    # Instrumented opcodes are at the end of the valid range
    min_internal = instmap["RESUME"] + 1
    min_instrumented = 254 - len(instrumented)
    assert min_internal + len(specialized) < min_instrumented

    next_opcode = 1

    def add_instruction(name: str) -> None:
        nonlocal next_opcode
        if name in instmap:
            return  # Pre-defined name
        while next_opcode in instmap.values():
            next_opcode += 1
        instmap[name] = next_opcode
        next_opcode += 1

    for name in sorted(no_arg):
        add_instruction(name)
    for name in sorted(has_arg):
        add_instruction(name)
    # For compatibility
    next_opcode = min_internal
    for name in sorted(specialized):
        add_instruction(name)
    next_opcode = min_instrumented
    for name in instrumented:
        add_instruction(name)

    for name in instructions:
        instructions[name].opcode = instmap[name]

    for op, name in enumerate(sorted(pseudos), 256):
        instmap[name] = op
        pseudos[name].opcode = op

    return instmap, len(no_arg), min_instrumented