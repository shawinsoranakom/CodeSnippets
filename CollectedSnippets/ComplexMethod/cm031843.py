def uop_cache_info(uop: Uop) -> list[str] | None:
    if uop.name == "_SPILL_OR_RELOAD":
        return None
    if uop.properties.records_value:
        return None
    default = "{ -1, -1, -1 },\n"
    table_size = MAX_CACHED_REGISTER + 1
    entries = [ default ] * table_size
    low = MAX_CACHED_REGISTER+1
    high = -1
    defined = [ False ] * 4
    for inputs, outputs, exit_depth in get_uop_cache_depths(uop):
        entries[inputs] = f"{{ {outputs}, {exit_depth}, {uop.name}_r{inputs}{outputs} }},\n"
        if inputs < low:
            low = inputs
        if inputs > high:
            high = inputs
    best = [ str(low if i < low else (high if high < i else i)) for i in range(MAX_CACHED_REGISTER+1) ]

    return [ f".best = {{ {', '.join(best)} }},\n", ".entries = {\n",  ] + entries + [ "},\n" ]