def generate_tier1_cases(
    analysis: Analysis, outfile: TextIO, lines: bool
) -> None:
    out = CWriter(outfile, 2, lines)
    emitter = Emitter(out, analysis.labels)
    out.emit("\n")
    for name, inst in sorted(analysis.instructions.items()):
        out.emit("\n")
        out.emit(f"TARGET({name}) {{\n")
        popped = get_popped(inst, analysis)
        # We need to ifdef it because this breaks platforms
        # without computed gotos/tail calling.
        out.emit(f"#if _Py_TAIL_CALL_INTERP\n")
        out.emit(f"int opcode = {name};\n")
        out.emit(f"(void)(opcode);\n")
        out.emit(f"#endif\n")
        needs_this = uses_this(inst)
        unused_guard = "(void)this_instr;\n"
        if inst.properties.needs_prev:
            out.emit(f"_Py_CODEUNIT* const prev_instr = frame->instr_ptr;\n")

        if needs_this and not inst.is_target:
            out.emit(f"_Py_CODEUNIT* const this_instr = next_instr;\n")
            out.emit(unused_guard)
        if not inst.properties.no_save_ip:
            out.emit(f"frame->instr_ptr = next_instr;\n")

        out.emit(f"next_instr += {inst.size};\n")
        out.emit(f"INSTRUCTION_STATS({name});\n")
        if inst.is_target:
            out.emit(f"PREDICTED_{name}:;\n")
            if needs_this:
                out.emit(f"_Py_CODEUNIT* const this_instr = next_instr - {inst.size};\n")
                out.emit(unused_guard)
        if inst.properties.uses_opcode:
            out.emit(f"opcode = {name};\n")
        if inst.family is not None:
            out.emit(
                f"static_assert({inst.family.size} == {inst.size-1}"
                ', "incorrect cache size");\n'
            )
        declare_variables(inst, out)
        offset = 1  # The instruction itself
        stack = Stack()
        for part in inst.parts:
            if part.properties.records_value:
                continue
            # Only emit braces if more than one uop
            insert_braces = len([p for p in inst.parts if isinstance(p, Uop)]) > 1
            reachable, offset, stack = write_uop(part, emitter, offset, stack, inst, insert_braces)
        out.start_line()
        if reachable: # type: ignore[possibly-undefined]
            stack.flush(out)
            out.emit("DISPATCH();\n")
        out.start_line()
        out.emit("}")
        out.emit("\n")