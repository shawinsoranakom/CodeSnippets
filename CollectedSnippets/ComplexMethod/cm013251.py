def get_traced_sample_variant_pairs(device, dtype, op):
    # tuples of (variant, sample)
    outputs: list[tuple[Any, Any]] = []

    samples = op.sample_inputs(device, dtype)

    # Acquires variants to test
    func = op.get_op()
    method = op.get_method()
    variants = {
        # TODO: inplace tests currently fail, fix and add inplace variant
        'function': func, 'method': method,
    }

    # TODO: find better way to standardize on op registration itself..
    has_fake_function = op.name in ["resize_", 'resize_as_']

    if has_fake_function:
        variants = {'method': getattr(torch.Tensor, op.name)}

    # In eager mode, these ops can take (Tensor, bool) args; but in
    # JIT they can only take (Tensor, Scalar), and bool is not a
    # scalar in the JIT type system. So to test these in JIT, the bool
    # is converted to an int for the test.
    ops_with_unsupported_bool_args = [
        {
            "name": "div_floor_rounding",
            "arg_idx": [0],
        },
        {
            "name": "div_no_rounding_mode",
            "arg_idx": [0],
        },
        {
            "name": "div_trunc_rounding",
            "arg_idx": [0],
        },
        {
            "name": "index_fill",
            "arg_idx": [2],
        },
        {
            "name": "full_like",
            "arg_idx": [0],
        },
        {
            "name": "mul",
            "arg_idx": [0],
        },
        {
            "name": "new_full",
            "arg_idx": [1],
        },
    ]

    # doesn't support tracing
    if has_fake_function:
        return outputs

    for sample in samples:
        for variant in variants.values():
            if variant is None:
                continue

            if is_lambda(variant):
                continue

            matching_ops = filter(lambda x: op.formatted_name == x["name"], ops_with_unsupported_bool_args)
            for op_data in matching_ops:
                for idx in op_data["arg_idx"]:
                    args = list(sample.args)
                    if len(sample.args) > idx and isinstance(sample.args[idx], bool):
                        args[idx] = int(args[idx])
                    sample.args = tuple(args)

            outputs.append((variant, sample))

    return outputs