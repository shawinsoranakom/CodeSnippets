def sample_inputs__unsafe_masked_index_put_accumulate(op_info, device, dtype, requires_grad, **kwargs):
    make_arg = partial(make_tensor, device=device, dtype=dtype, requires_grad=requires_grad)

    def make_idx(n, m, dim, d):
        view_shape = [1] * dim
        view_shape[d] = n
        return make_tensor((n,), device=device, dtype=torch.int64, low=0, high=m).view(view_shape)

    cases = [
        ((S, S), S, (M, M)),
        ((S, S), M, (S, S + 1)),
        ((S, S, S), S, (M, M - 1, M + 1)),
    ]

    for c in cases:
        self_shape, high, idx_sizes = c
        dim = len(self_shape)
        indices = [make_idx(idx_sizes[d], high, dim, d) for d in range(dim)]
        masks = [torch.logical_and(idx >= 0, idx < self_shape[i]) for i, idx in enumerate(indices) if idx is not None]
        mask = functools.reduce(torch.logical_and, masks)
        values = make_arg(idx_sizes)
        if device == 'mps:0' and dtype in [torch.float16, torch.bfloat16]:
            # TestConsistencyMPS.test_output_match compares CPU to MPS results
            # Order of operations in GPU index_put_accumulate is not guaranteed,
            # which can result in significant divergence between sequential and parallel execution
            # Unless inputs are normalized
            values = torch.nn.functional.normalize(values)
        yield SampleInput(make_arg(self_shape), mask, indices, values)

        masks = [torch.logical_and(idx >= 1, idx < self_shape[i] - 1) for i, idx in enumerate(indices) if idx is not None]
        mask = functools.reduce(torch.logical_and, masks)
        yield SampleInput(make_arg(self_shape), mask, indices, values)