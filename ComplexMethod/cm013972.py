def fix_vars(
    instructions: list[Instruction],
    code_options: dict[str, Any],
    varname_from_oparg: Callable[..., Any] | None = None,
) -> None:
    # compute instruction arg from argval if arg is not provided
    names = {name: idx for idx, name in enumerate(code_options["co_names"])}

    def get_name_index(name: str) -> int:
        try:
            idx = names[name]
        except KeyError:
            # Add a missing item to co_names
            idx = names[name] = len(names)
            code_options["co_names"] = (*code_options["co_names"], name)
            assert len(code_options["co_names"]) == len(names)
        return idx

    if sys.version_info < (3, 11):
        assert varname_from_oparg is None
        varnames = {name: idx for idx, name in enumerate(code_options["co_varnames"])}
        freenames = {
            name: idx
            for idx, name in enumerate(
                code_options["co_cellvars"] + code_options["co_freevars"]
            )
        }
    else:
        assert callable(varname_from_oparg)
        allnames = {}
        for idx in itertools.count():
            try:
                name = varname_from_oparg(idx)
                allnames[name] = idx
            except IndexError:
                break
        varnames = {name: allnames[name] for name in code_options["co_varnames"]}
        freenames = {
            name: allnames[name]
            for name in code_options["co_cellvars"] + code_options["co_freevars"]
        }
    for i in range(len(instructions)):

        def should_compute_arg() -> bool:
            # argval is prioritized over arg
            return instructions[i].argval is not _NotProvided

        if instructions[i].opname == "LOAD_GLOBAL":
            # 3.11 LOAD_GLOBAL requires both arg and argval - see create_instruction
            assert instructions[i].argval is not _NotProvided
            if sys.version_info >= (3, 11):
                assert instructions[i].arg is not None
                instructions[i].arg = (get_name_index(instructions[i].argval) << 1) + (
                    cast(int, instructions[i].arg) % 2
                )
            else:
                instructions[i].arg = get_name_index(instructions[i].argval)
        elif instructions[i].opname == "LOAD_ATTR":
            # 3.12 LOAD_ATTR requires both arg and argval, like LOAD_GLOBAL
            assert instructions[i].argval is not _NotProvided
            if sys.version_info >= (3, 12):
                assert instructions[i].arg is not None
                instructions[i].arg = (get_name_index(instructions[i].argval) << 1) + (
                    cast(int, instructions[i].arg) % 2
                )
            else:
                instructions[i].arg = get_name_index(instructions[i].argval)
        elif instructions[i].opname == "LOAD_SUPER_ATTR":
            assert instructions[i].arg is not None
            assert instructions[i].argval is not _NotProvided
            # Copy low bit, force second bit on for explicit super (the "+ 2")
            instructions[i].arg = (
                (get_name_index(instructions[i].argval) << 2)
                + (cast(int, instructions[i].arg) % 2)
                + 2
            )
        elif instructions[i].opname in FUSED_INSTS:
            assert sys.version_info >= (3, 13)
            assert isinstance(instructions[i].argval, tuple)
            assert len(instructions[i].argval) == 2
            arg_tuple = tuple(
                varnames[name] if name in varnames else freenames[name]
                for name in instructions[i].argval
            )
            instructions[i].arg = (arg_tuple[0] << 4) + (arg_tuple[1] & 15)
        elif instructions[i].opcode in HAS_LOCAL:
            if should_compute_arg():
                if (
                    sys.version_info >= (3, 13)
                    and instructions[i].argval not in varnames
                ):
                    # instructions like LOAD_FAST used for both local and free vars
                    instructions[i].arg = freenames[instructions[i].argval]
                else:
                    instructions[i].arg = varnames[instructions[i].argval]
        elif instructions[i].opcode in HAS_NAME:
            if should_compute_arg():
                instructions[i].arg = get_name_index(instructions[i].argval)
        elif instructions[i].opcode in HAS_FREE:
            if should_compute_arg():
                instructions[i].arg = freenames[instructions[i].argval]
        elif instructions[i].opcode in HAS_CONST:
            # NOTE: only update argval if arg is not provided. This assumes
            # that any additions to co_consts are appended.
            if instructions[i].arg is None:
                # cannot use a dictionary since consts may not be hashable
                idx = get_const_index(code_options, instructions[i].argval)
                assert idx >= 0
                instructions[i].arg = idx