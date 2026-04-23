def reference_inputs_view_reshape(op, device, dtype, requires_grad, **kwargs):
    yield from sample_inputs_view_reshape(op, device, dtype, requires_grad, **kwargs)

    cases = (
        # a, b, is_tensor_supported
        ((125,), (25, 5), True),
        ((25, 25), (1, 5, 5, 1, 5, 1, 5, 1), True),
        ((16, 32), (2, 4, 1, 4, 4, 1, 4), True),
        ((16, 12), (12, 16), True),
        ((1, 16, 12), (12, 16), True),
        ((1, 5, 1, 5), (25, 1), True),
        ((2, 4, 2), (4, 4), True),
        ((1, 4), (1, 1, 2, 1, 2), True),
        ((3, 5, 7), (7, 5, 3), True),
        ((1,), (), False),  # empty
        ((5, 0, 2, 3), (5, 0, 2, 3), True),
        ((2, 1, 0, 3, 1), (5, 0), True),
        ((1,), (), False),  # empty
        ((4, 5, 6), (4, 5, 6, 1, 1, 1), True),
        ((), (1, 1, 1, 1), False),  # empty
    )

    irreversible_cases = (
        ((), (-1,), False),  # neg index, empty
        ((4, 7, 9, 1, 1), (1, 4, 3, -1, 1), False),  # neg index
    )

    make_arg = partial(make_tensor, dtype=dtype, device=device, requires_grad=requires_grad)
    for a, b, is_tensor_supported in cases:
        # skip unsupported cases
        if kwargs.get("tensor_arg") and not is_tensor_supported:
            continue

        if kwargs.get("tensor_arg"):
            # convert to tensor
            yield SampleInput(make_arg(a), args=(make_arg(b, requires_grad=False),))
            yield SampleInput(make_arg(b), args=(make_arg(a, requires_grad=False),))
        else:
            yield SampleInput(make_arg(a), args=(b,))
            yield SampleInput(make_arg(b), args=(a,))

    for a, b, is_tensor_supported in irreversible_cases:
        # skip unsupported cases
        if kwargs.get("tensor_arg") and not is_tensor_supported:
            continue

        # convert to tensor
        if kwargs.get("tensor_arg"):
            b = make_arg(b, requires_grad=False)

        yield SampleInput(make_arg(a), args=(b,))