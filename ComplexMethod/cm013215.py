def error_inputs_view_reshape(op, device, **kwargs):

    cases = (
        # a, b, is_tensor_supported
        # Reshape to different numel
        ((2,), (), False),  # empty
        ((1, 3, 0), (), False),  # empty
        ((4, 3), (4, 2), True),
        ((1, 3, 5), (5, 2, 2), True),
        # No valid inference
        ((1, 3, 5), (5, -1, 2), False),  # neg index
        # Two inferred shapes
        ((1, 3, 5), (5, -1, -1), False),  # neg index
        ((1), (0, -1), False),  # neg index
        ((0, 5), (0, -1), False),  # neg index
    )

    make_arg = partial(make_tensor, dtype=torch.float32, device=device, requires_grad=False)
    for a, b, is_tensor_supported in cases:
        # skip unsupported cases
        if kwargs.get("tensor_arg") and not is_tensor_supported:
            continue

        if b == (5, -1, -1):
            error_regex = "only one dimension can be inferred"
        elif a == (0, 5):
            error_regex = (r"cannot reshape tensor of 0 elements into shape "
                           r"\[0, -1\] because the unspecified dimension size "
                           r"-1 can be any value and is ambiguous")
        else:
            # to avoid having issues with a regex
            shape = ', '.join(map(str, b))
            size = a if type(a) is int else functools.reduce(operator.mul, a, 1)
            error_regex = rf"shape '\[{shape}\]' is invalid for input of size {size}"

        # convert to tensor
        if kwargs.get("tensor_arg"):
            b = make_arg(b, requires_grad=False)

        yield ErrorInput(SampleInput(make_arg(a), args=(b,)), error_type=Exception,
                         error_regex=error_regex)