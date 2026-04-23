def write_uop(
    uop: Part,
    emitter: Emitter,
    offset: int,
    stack: Stack,
    inst: Instruction,
    braces: bool,
) -> tuple[bool, int, Stack]:
    # out.emit(stack.as_comment() + "\n")
    if isinstance(uop, Skip):
        entries = "entries" if uop.size > 1 else "entry"
        emitter.emit(f"/* Skip {uop.size} cache {entries} */\n")
        return True, (offset + uop.size), stack
    if isinstance(uop, Flush):
        emitter.emit(f"// flush\n")
        stack.flush(emitter.out)
        return True, offset, stack
    locals: dict[str, Local] = {}
    emitter.out.start_line()
    if braces:
        emitter.out.emit(f"// {uop.name}\n")
        emitter.emit("{\n")
        stack._print(emitter.out)
    storage = Storage.for_uop(stack, uop, emitter.out)

    for cache in uop.caches:
        if cache.name != "unused":
            if cache.size == 4:
                type = "PyObject *"
                reader = "read_obj"
            else:
                type = f"uint{cache.size*16}_t "
                reader = f"read_u{cache.size*16}"
            emitter.emit(
                f"{type}{cache.name} = {reader}(&this_instr[{offset}].cache);\n"
            )
            if inst.family is None:
                emitter.emit(f"(void){cache.name};\n")
        offset += cache.size

    reachable, storage = emitter.emit_tokens(uop, storage, inst, False)
    if braces:
        emitter.out.start_line()
        emitter.emit("}\n")
    # emitter.emit(stack.as_comment() + "\n")
    return reachable, offset, storage.stack