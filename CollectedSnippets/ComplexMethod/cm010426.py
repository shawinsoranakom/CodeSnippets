def invoke_leaf_function_dense(
    real_fn_callable,
    fake_fn_callable,
    input_spec,
    mutated_arg_indices,
    *flat_args,
    requires_grad_indices="",
):
    from torch._dynamo import config as dynamo_config

    version_before = [
        arg._version if isinstance(arg, torch.Tensor) else 0 for arg in flat_args
    ]

    flat_args = tuple(
        arg.detach() if isinstance(arg, torch.Tensor) else arg for arg in flat_args
    )
    requires_grad_indices_set = _parse_mutated_arg_indices(requires_grad_indices)
    flat_args = tuple(
        arg.requires_grad_(True) if idx in requires_grad_indices_set else arg
        for idx, arg in enumerate(flat_args)
    )

    with unflatten_args_with_modules(flat_args, input_spec) as (args, kwargs):
        real_output = real_fn_callable(*args, **kwargs)

        _check_no_input_mutation(flat_args, version_before, mutated_arg_indices)

        if dynamo_config.leaf_function_validate_outputs:
            fake_output = fake_fn_callable(*args, **kwargs)
            _validate_outputs_match(fake_output, real_output)

    return real_output