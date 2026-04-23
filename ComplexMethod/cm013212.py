def reference_inputs_elementwise_ternary(op, device, dtype, requires_grad, *, sample_inputs_func, supports_scalars=False, **kwargs):
    yield from sample_inputs_func(op, device, dtype, requires_grad, **kwargs)

    make_arg = partial(make_tensor, device=device, dtype=dtype, requires_grad=requires_grad)
    make_scalar_tensor = partial(make_tensor, (), device='cpu', dtype=dtype, requires_grad=requires_grad)
    supported_dtypes = op.supported_dtypes(device)

    # broadcasting and oncontiguous cases
    cases = (
        ((4, 4), (4, 4), (4, 4)),
        ((4, 4), (1, 4, 4), (4, 4)),
        ((4, 4), (1, 4, 4), (4, 1, 4)),
        ((4, 4, 1), (1, 4, 4), (4, 4)),
        ((4, 1), (1, 4, 4), (1, 4)),
        ((4, 4), (), (4, 4)),
        ((4, 4), (), ()),
        ((), (4, 4), (1, 4, 4)),
    )

    for a, b, c in cases:
        yield SampleInput(make_arg(a), args=(make_arg(b), make_arg(c)))
        yield SampleInput(make_arg(a, noncontiguous=True),
                          args=(make_arg(b).transpose(0, -1), make_arg(c, noncontiguous=True).transpose(0, -1)))

    # scalar cases
    if supports_scalars:
        cases = [
            ((), 1, 2,),
            ((), 1., 2),
            ((4, 4), 1., 2,),
            ((3, 4), make_scalar_tensor(), make_scalar_tensor()),
        ]

        if torch.complex64 in supported_dtypes:
            cases.extend([
                ((3, 1, 4), complex(1, 2), 3.),
            ])

        for a, b, c in cases:
            yield SampleInput(make_arg(a), args=(b, c))

    # type promotion cases
    # int x float
    if torch.float in supported_dtypes and torch.long in supported_dtypes:
        a = make_arg((), dtype=torch.long)
        b = make_arg((1, 4), dtype=torch.float)
        c = make_arg((3, 4))

        cases = (
            (a, b, c),
            (c, a, b),
        )

        for a, b, c in cases:
            yield SampleInput(a, args=(b, c))

    # NaN propagation
    if dtype.is_floating_point or dtype.is_complex:
        nan = float('nan') if dtype.is_floating_point else complex(float('nan'), float('nan'))

        a = make_arg((12,))
        a[4] = nan
        a[7] = nan
        b = make_arg((12,))
        b[1] = nan
        b[7] = nan
        c = make_arg((12,))
        c[9] = nan

        yield SampleInput(a, args=(b, c))