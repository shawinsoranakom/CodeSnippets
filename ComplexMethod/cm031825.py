def write_uop(
    override: Uop | None,
    uop: Uop,
    out: CWriter,
    stack: Stack,
    debug: bool,
    skip_inputs: bool,
) -> None:
    locals: dict[str, Local] = {}
    prototype = override if override else uop
    try:
        out.start_line()
        if override:
            storage = Storage.for_uop(stack, prototype, out, check_liveness=False)
        if debug:
            args = []
            for input in prototype.stack.inputs:
                if not input.peek or override:
                    args.append(input.name)
            out.emit(f'DEBUG_PRINTF({", ".join(args)});\n')
        if override:
            idx = 0
            for cache in uop.caches:
                if cache.name != "unused":
                    if cache.size == 4:
                        type = cast = "PyObject *"
                    else:
                        type = f"uint{cache.size*16}_t "
                        cast = f"uint{cache.size*16}_t"
                    out.emit(f"{type}{cache.name} = ({cast})this_instr->operand{idx};\n")
                    idx += 1
        if override:
            emitter = OptimizerEmitter(out, {}, uop, stack.copy())
            # No reference management of inputs needed.
            for var in storage.inputs:  # type: ignore[possibly-undefined]
                var.in_local = False
            _, storage = emitter.emit_tokens(override, storage, None, False)
            out.start_line()
            storage.flush(out)
            out.start_line()
        else:
            emit_default(out, uop, stack)
            out.start_line()
            stack.flush(out)
    except StackError as ex:
        raise analysis_error(ex.args[0], prototype.body.open)