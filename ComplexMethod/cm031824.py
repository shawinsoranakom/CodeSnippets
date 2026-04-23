def emit_default(out: CWriter, uop: Uop, stack: Stack) -> None:
    null = CWriter.null()
    for var in reversed(uop.stack.inputs):
        stack.pop(var, null)
    offset = stack.base_offset - stack.physical_sp
    for var in uop.stack.outputs:
        if var.is_array() and not var.peek and not var.name == "unused":
            c_offset = offset.to_c()
            out.emit(f"{var.name} = &stack_pointer[{c_offset}];\n")
        offset = offset.push(var)
    for var in uop.stack.outputs:
        local = Local.undefined(var)
        stack.push(local)
        if var.name != "unused" and not var.peek:
            local.in_local = True
            if var.is_array():
                if var.size == "1":
                    out.emit(f"{var.name}[0] = sym_new_not_null(ctx);\n")
                else:
                    out.emit(f"for (int _i = {var.size}; --_i >= 0;) {{\n")
                    out.emit(f"{var.name}[_i] = sym_new_not_null(ctx);\n")
                    out.emit("}\n")
            elif var.name == "null":
                out.emit(f"{var.name} = sym_new_null(ctx);\n")
            else:
                out.emit(f"{var.name} = sym_new_not_null(ctx);\n")