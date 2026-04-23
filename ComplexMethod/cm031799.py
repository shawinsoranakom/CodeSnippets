def analyze_stack(
    op: parser.InstDef | parser.Pseudo, replace_op_arg_1: str | None = None
) -> StackEffect:
    inputs: list[StackItem] = [
        convert_stack_item(i, replace_op_arg_1)
        for i in op.inputs
        if isinstance(i, parser.StackEffect)
    ]
    outputs: list[StackItem] = [
        convert_stack_item(i, replace_op_arg_1) for i in op.outputs
    ]
    # Mark variables with matching names at the base of the stack as "peek"
    modified = False
    input_names: dict[str, lexer.Token] = { i.name : i.first_token for i in op.inputs if i.name != "unused" }
    for input, output in itertools.zip_longest(inputs, outputs):
        if output is None:
            pass
        elif input is None:
            if output.name in input_names:
                raise analysis_error(
                    f"Reuse of variable '{output.name}' at different stack location",
                    input_names[output.name])
        elif input.name == output.name:
            if not modified:
                input.peek = output.peek = True
        else:
            modified = True
            if output.name in input_names:
                raise analysis_error(
                    f"Reuse of variable '{output.name}' at different stack location",
                    input_names[output.name])
    if isinstance(op, parser.InstDef):
        output_names = [out.name for out in outputs]
        for input in inputs:
            if (
                variable_used(op, input.name)
                or variable_used(op, "DECREF_INPUTS")
                or (not input.peek and input.name in output_names)
            ):
                input.used = True
        for output in outputs:
            if variable_used(op, output.name):
                output.used = True
    check_unused(inputs, input_names)
    return StackEffect(inputs, outputs)