def generate_tier2(
    filenames: list[str], analysis: Analysis, outfile: TextIO, lines: bool
) -> None:
    write_header(__file__, filenames, outfile)
    outfile.write(
        """
#ifdef TIER_ONE
    #error "This file is for Tier 2 only"
#endif
#define TIER_TWO 2
"""
    )
    out = CWriter(outfile, 2, lines)
    out.emit("\n")

    for name, uop in analysis.uops.items():
        if uop.properties.tier == 1:
            continue
        if uop.is_super():
            continue
        if uop.properties.records_value:
            continue
        why_not_viable = uop.why_not_viable()
        if why_not_viable is not None:
            out.emit(
                f"/* {uop.name} is not a viable micro-op for tier 2 because it {why_not_viable} */\n\n"
            )
            continue
        for inputs, outputs, exit_depth in get_uop_cache_depths(uop):
            emitter = Tier2Emitter(out, analysis.labels, exit_depth)
            out.emit(f"case {uop.name}_r{inputs}{outputs}: {{\n")
            out.emit(f"CHECK_CURRENT_CACHED_VALUES({inputs});\n")
            out.emit("assert(WITHIN_STACK_BOUNDS_IGNORING_CACHE());\n")
            declare_variables(uop, out)
            stack = Stack()
            stack.push_cache([f"_tos_cache{i}" for i in range(inputs)], out)
            stack._print(out)
            reachable, stack = write_uop(uop, emitter, stack, outputs)
            out.start_line()
            if reachable:
                out.emit("assert(WITHIN_STACK_BOUNDS_IGNORING_CACHE());\n")
                if not uop.properties.always_exits:
                    out.emit("break;\n")
            out.start_line()
            out.emit("}")
            out.emit("\n\n")
    out.emit("\n")
    outfile.write("#undef TIER_TWO\n")