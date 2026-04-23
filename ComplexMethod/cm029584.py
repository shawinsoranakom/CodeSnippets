def _get_instructions_bytes(code, linestarts=None, line_offset=0, co_positions=None,
                            original_code=None, arg_resolver=None):
    """Iterate over the instructions in a bytecode string.

    Generates a sequence of Instruction namedtuples giving the details of each
    opcode.

    """
    # Use the basic, unadaptive code for finding labels and actually walking the
    # bytecode, since replacements like ENTER_EXECUTOR and INSTRUMENTED_* can
    # mess that logic up pretty badly:
    original_code = original_code or code
    co_positions = co_positions or iter(())

    starts_line = False
    local_line_number = None
    line_number = None
    for offset, start_offset, op, arg in _unpack_opargs(original_code):
        if linestarts is not None:
            starts_line = offset in linestarts
            if starts_line:
                local_line_number = linestarts[offset]
            if local_line_number is not None:
                line_number = local_line_number + line_offset
            else:
                line_number = None
        positions = Positions(*next(co_positions, ()))
        deop = _deoptop(op)
        op = code[offset]

        if arg_resolver:
            argval, argrepr = arg_resolver.get_argval_argrepr(op, arg, offset)
        else:
            argval, argrepr = arg, repr(arg)

        caches = _get_cache_size(_all_opname[deop])
        # Advance the co_positions iterator:
        for _ in range(caches):
            next(co_positions, ())

        if caches:
            cache_info = []
            cache_offset = offset
            for name, size in _cache_format[opname[deop]].items():
                data = code[cache_offset + 2: cache_offset + 2 + 2 * size]
                cache_offset += size * 2
                cache_info.append((name, size, data))
        else:
            cache_info = None

        label = arg_resolver.get_label_for_offset(offset) if arg_resolver else None
        yield Instruction(_all_opname[op], op, arg, argval, argrepr,
                          offset, start_offset, starts_line, line_number,
                          label, positions, cache_info)