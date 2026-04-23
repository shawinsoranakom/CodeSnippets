def write_tailcall_dispatch_table(analysis: Analysis, out: CWriter) -> None:
    out.emit("static py_tail_call_funcptr instruction_funcptr_handler_table[256];\n")
    out.emit("\n")
    out.emit("static py_tail_call_funcptr instruction_funcptr_tracing_table[256];\n")
    out.emit("\n")

    # Emit function prototypes for labels.
    for name in analysis.labels:
        out.emit(f"{function_proto(name)};\n")
    out.emit("\n")

    # Emit function prototypes for opcode handlers.
    for name in sorted(analysis.instructions.keys()):
        out.emit(f"{function_proto(name)};\n")
    out.emit("\n")

    # Emit unknown opcode handler.
    out.emit(function_proto("UNKNOWN_OPCODE"))
    out.emit(" {\n")
    out.emit("int opcode = next_instr->op.code;\n")
    out.emit(UNKNOWN_OPCODE_HANDLER)
    out.emit("}\n")
    out.emit("\n")

    # Emit the dispatch table.
    out.emit("static py_tail_call_funcptr instruction_funcptr_handler_table[256] = {\n")
    for name in sorted(analysis.instructions.keys()):
        out.emit(f"[{name}] = _TAIL_CALL_{name},\n")
    named_values = analysis.opmap.values()
    for rest in range(256):
        if rest not in named_values:
            out.emit(f"[{rest}] = _TAIL_CALL_UNKNOWN_OPCODE,\n")
    out.emit("};\n")

    # Emit the tracing dispatch table.
    out.emit("static py_tail_call_funcptr instruction_funcptr_tracing_table[256] = {\n")
    for name in sorted(analysis.instructions.keys()):
        out.emit(f"[{name}] = _TAIL_CALL_TRACE_RECORD,\n")
    named_values = analysis.opmap.values()
    for rest in range(256):
        if rest not in named_values:
            out.emit(f"[{rest}] = _TAIL_CALL_UNKNOWN_OPCODE,\n")
    out.emit("};\n")
    outfile.write("#endif /* _Py_TAIL_CALL_INTERP */\n")