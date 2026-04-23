def sample_inputs_block_diag(op_info, device, dtype, requires_grad, **kwargs):
    make_arg = partial(make_tensor, dtype=dtype, device=device, requires_grad=requires_grad)
    test_cases: tuple[tuple] = (
        ((1, S), (2, S), (3, S),),
        ((S, 1), (S, 2), (S, 3),),
        ((1,), (2,), (3,),),
        ((2, S), (S,))
    )

    for shape, *other_shapes in test_cases:
        yield SampleInput(make_arg(shape), args=tuple(make_arg(s) for s in other_shapes))
        # We also want to test mixed complex-non-complex inputs to block_diag
        if dtype == torch.complex32 or dtype == torch.complex64:
            non_complex_dtype = torch.float32 if dtype == torch.complex32 or device == 'mps:0' else torch.float64
            make_arg_non_complex = partial(make_tensor, dtype=non_complex_dtype, device=device, requires_grad=requires_grad)
            yield SampleInput(make_arg_non_complex(shape), args=tuple(make_arg(s) for s in other_shapes))