def generate_abstract_interpreter(
    filenames: list[str],
    abstract: Analysis,
    base: Analysis,
    outfile: TextIO,
    debug: bool,
) -> None:
    write_header(__file__, filenames, outfile)
    out = CWriter(outfile, 2, False)
    out.emit("\n")
    base_uop_names = set([uop.name for uop in base.uops.values()])
    for abstract_uop_name in abstract.uops:
        if abstract_uop_name not in base_uop_names:
            raise ValueError(f"All abstract uops should override base uops, "
                                 f"but {abstract_uop_name} is not.")

    for uop in base.uops.values():
        override: Uop | None = None
        if uop.name in abstract.uops:
            override = abstract.uops[uop.name]
            validate_uop(override, uop)
        if uop.properties.tier == 1:
            continue
        if uop.replicates:
            continue
        if uop.is_super():
            continue
        if not uop.is_viable():
            out.emit(f"/* {uop.name} is not a viable micro-op for tier 2 */\n\n")
            continue
        out.emit(f"case {uop.name}: {{\n")
        if override:
            declare_variables(override, out, skip_inputs=False)
        else:
            declare_variables(uop, out, skip_inputs=True)
        stack = Stack(check_stack_bounds=True)
        write_uop(override, uop, out, stack, debug, skip_inputs=(override is None))
        out.start_line()
        out.emit("break;\n")
        out.emit("}")
        out.emit("\n\n")