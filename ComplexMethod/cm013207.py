def sample_inputs_index_reduce(op_info, device, dtype, requires_grad, **kwargs):
    make_arg = partial(make_tensor, device=device, dtype=dtype, requires_grad=requires_grad)

    def make_idx(n, m):
        return make_tensor((n,), device=device, dtype=torch.int64, low=0, high=m)

    shapes = [((), ()), ((1,), (1,)), ((S, S), (S, M)), ((S, S, S), (S, M, S))]
    include_selfs = (True, False)
    reduce = op_info.variant_test_name
    if reduce not in ('prod', 'mean', 'amin', 'amax'):
        raise AssertionError(f"Expected reduce to be one of 'prod', 'mean', 'amin', 'amax', got {reduce!r}")

    for shape, include_self in product(shapes, include_selfs):
        self_shape, src_shape = shape
        # dim. We handle the scalar case
        dim = 1 if len(self_shape) >= 2 else 0
        idx = make_idx(src_shape[dim] if len(src_shape) != 0 else 1,
                       self_shape[dim] if len(self_shape) != 0 else 1)
        args = (dim, idx, make_arg(src_shape), reduce)
        yield SampleInput(make_arg(self_shape),
                          args=args,
                          kwargs={'include_self' : include_self})

    # Sample inputs to test edge cases for backward
    if requires_grad and reduce == 'prod':
        # Check that gradients are propagated correctly for prod when zeros in self/src are reduced
        # This sample tests gradients for the following cases
        # (a) 1 zero reduced (from source (self[0, 1]), from self (self[0, 0]))
        # (b) 2 zeros reduced (1 from src and 1 from self (self[1, 0], self[1, 1])
        # (c) no zeros reduced (self[2, 1], self[2, 2])
        # (d) 2 zeros reduced (both from src) is tested in test/test_autograd.py
        #     test_scatter_index_reduce_prod_gradgrad_error as this case is not supported for gradgrad
        input = torch.tensor([[0, 13], [0, 0], [15, 19]], dtype=dtype, device=device, requires_grad=requires_grad)
        src = torch.tensor([[2, 0], [0, 0], [2, 3], [2, 2]], dtype=dtype, device=device, requires_grad=requires_grad)
        idx = torch.tensor([0, 1, 2, 0], dtype=torch.long, device=device)

        yield SampleInput(input,
                          args=(0, idx, src, reduce),
                          kwargs={'include_self': True})