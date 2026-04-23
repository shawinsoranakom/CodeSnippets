def generate_uop_ids(
    filenames: list[str], analysis: Analysis, outfile: TextIO, distinct_namespace: bool
) -> None:
    write_header(__file__, filenames, outfile)
    out = CWriter(outfile, 0, False)
    with out.header_guard("Py_CORE_UOP_IDS_H"):
        next_id = 1 if distinct_namespace else 300
        # These two are first by convention
        out.emit(f"#define _EXIT_TRACE {next_id}\n")
        next_id += 1
        out.emit(f"#define _SET_IP {next_id}\n")
        next_id += 1
        PRE_DEFINED = {"_EXIT_TRACE", "_SET_IP"}

        uops = [(uop.name, uop) for uop in analysis.uops.values()]
        # Sort so that _BASE comes immediately before _BASE_0, etc.
        for name, uop in sorted(uops):
            if name in PRE_DEFINED or uop.is_super() or uop.properties.tier == 1:
                continue
            if uop.implicitly_created and not distinct_namespace and not uop.replicated:
                out.emit(f"#define {name} {name[1:]}\n")
            else:
                out.emit(f"#define {name} {next_id}\n")
                next_id += 1

        out.emit(f"#define MAX_UOP_ID {next_id-1}\n")
        for name, uop in sorted(uops):
            if uop.properties.tier == 1:
                continue
            if uop.properties.records_value:
                continue
            for inputs, outputs, _ in sorted(get_uop_cache_depths(uop)):
                out.emit(f"#define {name}_r{inputs}{outputs} {next_id}\n")
                next_id += 1
        out.emit(f"#define MAX_UOP_REGS_ID {next_id-1}\n")