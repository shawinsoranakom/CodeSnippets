def sample_inputs_addcmul_addcdiv(op_info, device, dtype, requires_grad, **kwargs):
    make_arg = partial(make_tensor, device=device, dtype=dtype, requires_grad=requires_grad)
    test_cases = [(((S, S), (S, S), (S, S)), False),
                  (((S, S), (S, 1), (1, S)), False),
                  (((1,), (S, S, 1), (1, S)), True),
                  (((), (), ()), False),
                  (((S, S), (), ()), True),
                  (((), (S, S, 1), (1, S)), True)
                  ]

    for input_args, broadcasts_input in test_cases:
        # addcdiv should accept inputs with zero value
        # Currently, it throws ZeroDivisionError when the denominator is zero
        # TODO: exclude_zeros can be removed after https://github.com/pytorch/pytorch/issues/73638 is fixed
        args = tuple(make_arg(arg, exclude_zero=True) if isinstance(arg, tuple) else arg
                     for arg in input_args)
        yield SampleInput(*args).with_metadata(broadcasts_input=broadcasts_input)

        # addcdiv should accept inputs with zero value
        # Currently, it throws ZeroDivisionError when the denominator is zero
        # TODO: exclude_zeros can be removed after https://github.com/pytorch/pytorch/issues/73638 is fixed
        args = tuple(make_arg(arg, exclude_zero=True) if isinstance(arg, tuple) else arg
                     for arg in input_args)
        yield SampleInput(
            *args, value=3.14 if dtype.is_floating_point or dtype.is_complex else 3
        ).with_metadata(broadcasts_input=broadcasts_input)