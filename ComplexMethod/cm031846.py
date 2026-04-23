def generate_deopt_table(analysis: Analysis, out: CWriter) -> None:
    out.emit("PyAPI_DATA(const uint8_t) _PyOpcode_Deopt[256];\n")
    out.emit("#ifdef NEED_OPCODE_METADATA\n")
    out.emit("const uint8_t _PyOpcode_Deopt[256] = {\n")
    deopts: list[tuple[str, str]] = []
    for inst in analysis.instructions.values():
        deopt = inst.name
        if inst.family is not None:
            deopt = inst.family.name
        deopts.append((inst.name, deopt))
    defined = set(analysis.opmap.values())
    for i in range(256):
        if i not in defined:
            deopts.append((f'{i}', f'{i}'))

    assert len(deopts) == 256
    assert len(set(x[0] for x in deopts)) == 256
    for name, deopt in sorted(deopts):
        out.emit(f"[{name}] = {deopt},\n")
    out.emit("};\n\n")
    out.emit("#endif // NEED_OPCODE_METADATA\n\n")