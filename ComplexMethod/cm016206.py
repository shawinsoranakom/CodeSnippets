def _get_template_filtered_operators(
    template: str = "default", supported_ops: list[str] | None = None
):
    """Get operators filtered by template's supported_ops, with user override.

    If supported_ops is provided, it takes precedence and is used to filter the
    registry. Otherwise, the template's supported_ops are used. If neither are
    specified, all operators are returned.
    """
    # Instantiate template
    if template == "dtensor":
        from torchfuzz.codegen import DTensorFuzzTemplate

        fuzz_template = DTensorFuzzTemplate()
    elif template == "dtensor_placements":
        from torchfuzz.codegen import DTensorFuzzPlacementsTemplate

        fuzz_template = DTensorFuzzPlacementsTemplate()
    elif template == "unbacked":
        from torchfuzz.codegen import UnbackedFuzzTemplate

        fuzz_template = UnbackedFuzzTemplate()
    elif template == "streams":
        from torchfuzz.codegen import StreamFuzzTemplate

        fuzz_template = StreamFuzzTemplate()
    else:
        from torchfuzz.codegen import DefaultFuzzTemplate

        fuzz_template = DefaultFuzzTemplate()

    all_operators = _get_cached_operators()

    # Determine allowed ops list
    allowed_ops = supported_ops if supported_ops else fuzz_template.supported_ops

    # If no supported_ops specified, return all operators
    if not allowed_ops:
        return all_operators

    # Filter operators based on allowed_ops
    filtered_ops = {}

    for op_name, operator in all_operators.items():
        # Always include operations that don't have a specific torch operation
        # (utility operations like arg, constant, item, scalar ops)
        torch_op = operator.torch_op_name
        if torch_op is None:
            # Set template on operators that support it
            if hasattr(operator, "set_template"):
                operator.set_template(template)  # type: ignore[attr-defined]
            filtered_ops[op_name] = operator
            continue

        # Check if the operator supports any of the allowed operations
        should_include = False
        for supported_op in allowed_ops:
            # Direct torch operation matching
            if torch_op == supported_op:
                should_include = True
                break

            # Direct name matching as fallback
            if supported_op in op_name or op_name in supported_op:
                should_include = True
                break

        if should_include:
            # Set template on operators that support it
            if hasattr(operator, "set_template"):
                operator.set_template(template)  # type: ignore[attr-defined]
            filtered_ops[op_name] = operator

    return filtered_ops