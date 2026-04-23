def create_forward_derivative(
    f: NativeFunction, formula: str, names: tuple[str, ...]
) -> ForwardDerivative:
    var_names = names
    var_types: tuple[Type, ...] | None = None
    for r in f.func.returns:
        if r.name in var_names:
            if var_types is None:
                var_types = ()
            var_types = var_types + (r.type,)

    # Handle default return names
    if var_types is None:
        if var_names == ("result",):
            if len(f.func.returns) != 1:
                raise AssertionError(
                    f"Expected 1 return for 'result', got {len(f.func.returns)}"
                )
            var_types = (f.func.returns[0].type,)
        else:
            for var_name in var_names:
                res = re.findall(r"^result(\d+)$", var_name)
                if len(res) == 1:
                    if var_types is None:
                        var_types = ()
                    arg_idx = int(res[0])
                    var_types = var_types + (f.func.returns[arg_idx].type,)

    if var_types is None:
        raise AssertionError("No matching output for forward derivative definition")
    return ForwardDerivative(
        formula=formula,
        var_names=var_names,
        var_types=var_types,
        required_inputs_fw_grad=None,
        required_inputs_primal=None,
        required_original_self_value=False,
        is_reusing_outplace_formula=False,
    )