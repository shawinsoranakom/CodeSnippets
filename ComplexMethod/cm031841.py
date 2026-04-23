def write_uop(uop: Uop, emitter: Tier2Emitter, stack: Stack, cached_items: int = 0) -> tuple[bool, Stack]:
    locals: dict[str, Local] = {}
    zero_regs = is_large(uop) or uop.properties.escapes
    try:
        emitter.out.start_line()
        if uop.properties.oparg:
            emitter.emit("oparg = CURRENT_OPARG();\n")
            assert uop.properties.const_oparg < 0
        elif uop.properties.const_oparg >= 0:
            emitter.emit(f"oparg = {uop.properties.const_oparg};\n")
            emitter.emit(f"assert(oparg == CURRENT_OPARG());\n")
        storage = Storage.for_uop(stack, uop, emitter.out)
        idx = 0
        for cache in uop.caches:
            if cache.name != "unused":
                bits = cache.size*16
                if cache.size == 4:
                    type = cast = "PyObject *"
                else:
                    type = f"uint{bits}_t "
                    cast = f"uint{bits}_t"
                emitter.emit(f"{type}{cache.name} = ({cast})CURRENT_OPERAND{idx}_{bits}();\n")
                idx += 1
        reachable, storage = emitter.emit_tokens(uop, storage, None, False)
        if reachable:
            storage.stack._print(emitter.out)
            emitter.cache_items(storage.stack, cached_items, zero_regs)
            storage.flush(emitter.out)
        return reachable, storage.stack
    except StackError as ex:
        raise analysis_error(ex.args[0], uop.body.open) from None