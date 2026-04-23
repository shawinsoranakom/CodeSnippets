def declare_variables(uop: Uop, out: CWriter, skip_inputs: bool) -> None:
    variables = {"unused"}
    if not skip_inputs:
        for var in reversed(uop.stack.inputs):
            if var.used and var.name not in variables:
                variables.add(var.name)
                out.emit(f"{type_name(var)}{var.name};\n")
    for var in uop.stack.outputs:
        if var.peek:
            continue
        if var.name not in variables:
            variables.add(var.name)
            out.emit(f"{type_name(var)}{var.name};\n")