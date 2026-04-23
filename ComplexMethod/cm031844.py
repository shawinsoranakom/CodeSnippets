def generate_names_and_flags(analysis: Analysis, out: CWriter) -> None:
    out.emit(f"#define MAX_CACHED_REGISTER {MAX_CACHED_REGISTER}\n")
    out.emit("extern const uint32_t _PyUop_Flags[MAX_UOP_ID+1];\n")
    out.emit("typedef struct _rep_range { uint8_t start; uint8_t stop; } ReplicationRange;\n")
    out.emit("extern const ReplicationRange _PyUop_Replication[MAX_UOP_ID+1];\n")
    out.emit("extern const char * const _PyOpcode_uop_name[MAX_UOP_REGS_ID+1];\n\n")
    out.emit("extern int _PyUop_num_popped(int opcode, int oparg);\n")
    out.emit(CACHING_INFO_DECL)
    out.emit(f"extern const uint16_t _PyUop_SpillsAndReloads[{MAX_CACHED_REGISTER+1}][{MAX_CACHED_REGISTER+1}];\n")
    out.emit("extern const uint16_t _PyUop_Uncached[MAX_UOP_REGS_ID+1];\n\n")
    out.emit("#ifdef NEED_OPCODE_METADATA\n")
    out.emit("const uint32_t _PyUop_Flags[MAX_UOP_ID+1] = {\n")
    for uop in analysis.uops.values():
        if uop.is_viable() and uop.properties.tier != 1 and not uop.is_super():
            out.emit(f"[{uop.name}] = {cflags(uop.properties)},\n")

    out.emit("};\n\n")
    out.emit("const ReplicationRange _PyUop_Replication[MAX_UOP_ID+1] = {\n")
    for uop in analysis.uops.values():
        if uop.replicated:
            assert(uop.replicated.step == 1)
            out.emit(f"[{uop.name}] = {{ {uop.replicated.start}, {uop.replicated.stop} }},\n")

    out.emit("};\n\n")
    out.emit("const _PyUopCachingInfo _PyUop_Caching[MAX_UOP_ID+1] = {\n")
    for uop in analysis.uops.values():
        if uop.is_viable() and uop.properties.tier != 1 and not uop.is_super():
            info = uop_cache_info(uop)
            if info is not None:
                out.emit(f"[{uop.name}] = {{\n")
                for line in info:
                    out.emit(line)
                out.emit("},\n")
    out.emit("};\n\n")
    out.emit("const uint16_t _PyUop_Uncached[MAX_UOP_REGS_ID+1] = {\n");
    for uop in analysis.uops.values():
        if uop.is_viable() and uop.properties.tier != 1 and not uop.is_super() and not uop.properties.records_value:
            for inputs, outputs, _ in get_uop_cache_depths(uop):
                out.emit(f"[{uop.name}_r{inputs}{outputs}] = {uop.name},\n")
    out.emit("};\n\n")
    out.emit(f"const uint16_t _PyUop_SpillsAndReloads[{MAX_CACHED_REGISTER+1}][{MAX_CACHED_REGISTER+1}] = {{\n")
    for i in range(MAX_CACHED_REGISTER+1):
        for j in range(MAX_CACHED_REGISTER+1):
            if i != j:
                out.emit(f"[{i}][{j}] = _SPILL_OR_RELOAD_r{i}{j},\n")
    out.emit("};\n\n")
    out.emit("const char *const _PyOpcode_uop_name[MAX_UOP_REGS_ID+1] = {\n")
    for uop in sorted(analysis.uops.values(), key=lambda t: t.name):
        if uop.is_viable() and uop.properties.tier != 1 and not uop.is_super():
            out.emit(f'[{uop.name}] = "{uop.name}",\n')
            if not uop.properties.records_value:
                for inputs, outputs, _ in get_uop_cache_depths(uop):
                    out.emit(f'[{uop.name}_r{inputs}{outputs}] = "{uop.name}_r{inputs}{outputs}",\n')
    out.emit("};\n")
    out.emit("int _PyUop_num_popped(int opcode, int oparg)\n{\n")
    out.emit("switch(opcode) {\n")
    null = CWriter.null()
    for uop in analysis.uops.values():
        if uop.is_viable() and uop.properties.tier != 1 and not uop.is_super():
            stack = Stack()
            for var in reversed(uop.stack.inputs):
                if var.peek:
                    break
                stack.pop(var, null)
            popped = (-stack.base_offset).to_c()
            out.emit(f"case {uop.name}:\n")
            out.emit(f"    return {popped};\n")
    out.emit("default:\n")
    out.emit("    return -1;\n")
    out.emit("}\n")
    out.emit("}\n\n")
    out.emit("#endif // NEED_OPCODE_METADATA\n\n")