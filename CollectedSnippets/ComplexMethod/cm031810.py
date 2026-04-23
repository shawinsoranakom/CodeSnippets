def get_uop_cache_depths(uop: Uop) -> Iterator[tuple[int, int, int]]:
    if uop.name == "_SPILL_OR_RELOAD":
        for inputs in range(MAX_CACHED_REGISTER+1):
            for outputs in range(MAX_CACHED_REGISTER+1):
                if inputs != outputs:
                    yield inputs, outputs, inputs
        return
    if uop.name in ("_DEOPT", "_HANDLE_PENDING_AND_DEOPT", "_EXIT_TRACE", "_DYNAMIC_EXIT"):
        for i in range(MAX_CACHED_REGISTER+1):
            yield i, 0, 0
        return
    if uop.name in ("_START_EXECUTOR", "_JUMP_TO_TOP", "_COLD_EXIT"):
        yield 0, 0, 0
        return
    if uop.name == "_ERROR_POP_N":
        yield 0, 0, 0
        return
    ideal_inputs = 0
    has_array = False
    for item in reversed(uop.stack.inputs):
        if item.size:
            has_array = True
            break
        ideal_inputs += 1
    ideal_outputs = 0
    for item in reversed(uop.stack.outputs):
        if item.size:
            has_array = True
            break
        ideal_outputs += 1
    if ideal_inputs > MAX_CACHED_REGISTER:
        ideal_inputs = MAX_CACHED_REGISTER
    if ideal_outputs > MAX_CACHED_REGISTER:
        ideal_outputs = MAX_CACHED_REGISTER
    at_end = uop.properties.sync_sp or uop.properties.side_exit_at_end
    exit_depth = ideal_outputs if at_end else ideal_inputs
    if uop.properties.escapes or uop.properties.sync_sp or has_array or is_large(uop):
        yield ideal_inputs, ideal_outputs, exit_depth
        return
    for inputs in range(MAX_CACHED_REGISTER + 1):
        outputs = ideal_outputs - ideal_inputs + inputs
        if outputs < ideal_outputs:
            outputs = ideal_outputs
        elif outputs > MAX_CACHED_REGISTER:
            continue
        yield inputs, outputs, outputs if at_end else inputs