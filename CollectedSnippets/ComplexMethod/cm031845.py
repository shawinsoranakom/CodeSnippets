def generate_recorder_tables(analysis: Analysis, out: CWriter) -> None:
    record_function_indexes: dict[str, int] = dict()
    record_table: dict[str, list[str]] = {}
    index = 1
    for inst in analysis.instructions.values():
        if not inst.properties.records_value:
            continue
        records: list[str] = []
        for part in inst.parts:
            if not part.properties.records_value:
                continue
            if part.name not in record_function_indexes:
                record_function_indexes[part.name] = index
                index += 1
            records.append(part.name)
        if records:
            if len(records) > MAX_RECORDED_VALUES:
                raise ValueError(
                    f"Instruction {inst.name} has {len(records)} recording ops, "
                    f"exceeds MAX_RECORDED_VALUES ({MAX_RECORDED_VALUES})"
                )
            record_table[inst.name] = records
    func_count = len(record_function_indexes)

    for name, index in record_function_indexes.items():
        out.emit(f"#define {name}_INDEX {index}\n")
    out.emit("\n")
    out.emit("const _PyOpcodeRecordEntry _PyOpcode_RecordEntries[256] = {\n")
    for inst_name, record_names in record_table.items():
        indices = ", ".join(f"{name}_INDEX" for name in record_names)
        out.emit(f"    [{inst_name}] = {{{len(record_names)}, {{{indices}}}}},\n")
    out.emit("};\n\n")
    out.emit(f"const _Py_RecordFuncPtr _PyOpcode_RecordFunctions[{func_count+1}] = {{\n")
    out.emit("    [0] = NULL,\n")
    for name in record_function_indexes:
        out.emit(f"    [{name}_INDEX] = _PyOpcode_RecordFunction{name[7:]},\n")
    out.emit("};\n")