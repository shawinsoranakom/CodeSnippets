def signatures_match(decomposition_sig, torch_op_sig):
    decomp_params = decomposition_sig.parameters
    op_params = torch_op_sig.parameters

    if len(decomp_params) != len(op_params):
        return False

    for decomp_param, op_param in zip(decomp_params.values(), op_params.values()):
        # can't check full equality yet because not all fields are correctly deduced
        # in the torch_op_sig - like default value
        # can't check 'kind' bc
        # kwarg-only values with defaults not yet supported in TS
        inspect_empty = inspect._empty  # type: ignore[attr-defined]
        for field in ["name", "annotation"]:
            if field == "name" and decomp_param.name == "self":
                warnings.warn(
                    "PyTorch uses 'input' instead of 'self' on public api", stacklevel=2
                )

            if getattr(decomp_param, field) != getattr(op_param, field):
                return False

        decomp_default = decomp_param.default
        op_default = op_param.default
        # default value not always correctly inferred as being present on torch schema,
        # but if specified on both they should be equal
        if decomp_default != inspect_empty and op_default != inspect_empty:
            if decomp_default != op_default:
                return False

    return decomposition_sig.return_annotation == torch_op_sig.return_annotation