def explicit_super(code: types.CodeType, instructions: list[Instruction]) -> None:
    """convert super() with no args into explicit arg form"""
    cell_and_free = (code.co_cellvars or ()) + (code.co_freevars or ())
    if not len(code.co_varnames):
        # A function with no argument cannot contain a valid "super()" call
        return
    output = []
    for idx, inst in enumerate(instructions):
        output.append(inst)
        if inst.opname == "LOAD_GLOBAL" and inst.argval == "super":
            nexti = instructions[idx + 1]
            if nexti.arg == 0 and (
                (sys.version_info >= (3, 12) and nexti.opname == "CALL")
                or (
                    sys.version_info >= (3, 11)
                    and sys.version_info < (3, 12)
                    and nexti.opname == "PRECALL"
                )
                or (sys.version_info < (3, 11) and nexti.opname == "CALL_FUNCTION")
            ):
                assert "__class__" in cell_and_free
                output.append(create_instruction("LOAD_DEREF", argval="__class__"))
                first_var = code.co_varnames[0]
                if first_var in cell_and_free:
                    output.append(create_instruction("LOAD_DEREF", argval=first_var))
                else:
                    output.append(create_instruction("LOAD_FAST", argval=first_var))
                nexti.arg = 2
                nexti.argval = 2
                if nexti.opname == "PRECALL":
                    # also update the following CALL instruction
                    call_inst = instructions[idx + 2]
                    call_inst.arg = 2
                    call_inst.argval = 2

    instructions[:] = output