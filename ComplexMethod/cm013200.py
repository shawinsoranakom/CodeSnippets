def sample_inputs_addmm(op_info, device, dtype, requires_grad, **kwargs):
    alpha_val = kwargs.get('alpha', 2 + 3j if dtype.is_complex else 0.6 if dtype.is_floating_point else 2)
    beta_val = kwargs.get('beta', 1 + 2j if dtype.is_complex else 0.2 if dtype.is_floating_point else 3)
    tests_list = [
        ((2, 3), (2, 2), (2, 3), False),
        ((3, 3), (3, 3), (3, 3), False),
    ]
    tests_with_lhs_broadcasting = [
        ((1,), (2, 2), (2, 3), True),
        ((), (2, 2), (2, 3), True),
    ]
    test_cases = tests_list + tests_with_lhs_broadcasting  # type: ignore[operator]

    kwargs = dict(alpha=alpha_val, beta=beta_val)
    make_arg = partial(make_tensor, dtype=dtype, device=device, requires_grad=requires_grad)
    for shape_a, shape_b, shape_c, broadcasts_input in test_cases:
        yield SampleInput(
            make_arg(shape_a),
            make_arg(shape_b),
            make_arg(shape_c),
            **kwargs,
        ).with_metadata(broadcasts_input=broadcasts_input)

    if dtype.is_complex:
        shape = (3, 3)
        yield SampleInput(
            make_arg(shape),
            make_arg(shape, requires_grad=False).mH.requires_grad_(requires_grad),
            make_arg(shape),
            **kwargs,
        )
        yield SampleInput(
            make_arg(shape),
            make_arg(shape),
            make_arg(shape, requires_grad=False).mH.requires_grad_(requires_grad),
            **kwargs,
        )
    # addmm of empty matrices
    if dtype.is_floating_point:
        yield SampleInput(make_arg(S, M), make_arg(S, 0), make_arg(0, M), **kwargs)
        # empty matmul with broadcastable input
        yield SampleInput(make_arg(M), make_arg(S, 0), make_arg(0, M), **kwargs).with_metadata(broadcasts_input=True)