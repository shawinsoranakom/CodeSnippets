def uses_this(inst: Instruction) -> bool:
    if inst.properties.needs_this:
        return True
    for uop in inst.parts:
        if not isinstance(uop, Uop):
            continue
        for cache in uop.caches:
            if cache.name != "unused":
                return True
    # Can't be merged into the loop above, because
    # this must strictly be performed at the end.
    for uop in inst.parts:
        if not isinstance(uop, Uop):
            continue
        for tkn in uop.body.tokens():
            if (tkn.kind == "IDENTIFIER"
                    and (tkn.text in {"DEOPT_IF", "EXIT_IF", "AT_END_EXIT_IF"})):
                return True
    return False