def generate_expansion_table(analysis: Analysis, out: CWriter) -> None:
    expansions_table: dict[str, list[tuple[str, str, int]]] = {}
    for inst in sorted(analysis.instructions.values(), key=lambda t: t.name):
        offset: int = 0  # Cache effect offset
        expansions: list[tuple[str, str, int]] = []  # [(name, size, offset), ...]
        if inst.is_super():
            pieces = inst.name.split("_")
            assert len(pieces) % 2 == 0, f"{inst.name} doesn't look like a super-instr"
            parts_per_piece = int(len(pieces) / 2)
            name1 = "_".join(pieces[:parts_per_piece])
            name2 = "_".join(pieces[parts_per_piece:])
            assert name1 in analysis.instructions, f"{name1} doesn't match any instr"
            assert name2 in analysis.instructions, f"{name2} doesn't match any instr"
            instr1 = analysis.instructions[name1]
            instr2 = analysis.instructions[name2]
            for part in instr1.parts:
                expansions.append((part.name, "OPARG_TOP", 0))
            for part in instr2.parts:
                expansions.append((part.name, "OPARG_BOTTOM", 0))
        elif not is_viable_expansion(inst):
            continue
        else:
            for part in inst.parts:
                size = part.size
                if isinstance(part, Uop):
                    # Skip specializations
                    if "specializing" in part.annotations:
                        continue
                    # Add the primary expansion.
                    fmt = "OPARG_SIMPLE"
                    if part.name == "_SAVE_RETURN_OFFSET":
                        fmt = "OPARG_SAVE_RETURN_OFFSET"
                    elif part.caches:
                        fmt = str(part.caches[0].size)
                    if "replaced" in part.annotations:
                        fmt = "OPARG_REPLACED"
                    expansions.append((part.name, fmt, offset))
                    if len(part.caches) > 1:
                        # Add expansion for the second operand
                        internal_offset = 0
                        for cache in part.caches[:-1]:
                            internal_offset += cache.size
                        expansions.append((part.name, f"OPERAND1_{part.caches[-1].size}", offset+internal_offset))
                offset += part.size
        expansions_table[inst.name] = expansions
    max_uops = max(len(ex) for ex in expansions_table.values())
    out.emit(f"#define MAX_UOP_PER_EXPANSION {max_uops}\n")
    out.emit("struct opcode_macro_expansion {\n")
    out.emit("int nuops;\n")
    out.emit(
        "struct { int16_t uop; int8_t size; int8_t offset; } uops[MAX_UOP_PER_EXPANSION];\n"
    )
    out.emit("};\n")
    out.emit(
        "extern const struct opcode_macro_expansion _PyOpcode_macro_expansion[256];\n\n"
    )
    out.emit("#ifdef NEED_OPCODE_METADATA\n")
    out.emit("const struct opcode_macro_expansion\n")
    out.emit("_PyOpcode_macro_expansion[256] = {\n")
    for inst_name, expansions in expansions_table.items():
        uops = [
            f"{{ {name}, {size}, {offset} }}" for (name, size, offset) in expansions
        ]
        out.emit(
            f'[{inst_name}] = {{ .nuops = {len(expansions)}, .uops = {{ {", ".join(uops)} }} }},\n'
        )
    out.emit("};\n")
    out.emit("#endif // NEED_OPCODE_METADATA\n\n")