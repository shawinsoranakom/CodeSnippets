def sample_inputs_put(op_info, device, dtype, requires_grad, **kwargs):
    make_arg = partial(make_tensor, dtype=dtype, device=device, requires_grad=requires_grad)
    make_idx = partial(make_tensor, low=0, dtype=torch.int64, device=device, requires_grad=False)

    S = 3

    # Generic inputs
    idx = torch.randperm(S * S, device=device, dtype=torch.int64)[:S]
    idx_list = [idx, -idx - 1]
    for idx, acc in product(idx_list, (True, False)):
        yield SampleInput(input=make_arg((S, S)),
                          args=(idx.clone(),
                                make_arg((S,)),
                                acc))

    # Scalar cases
    scalar_sizes = [(), (1,)]
    tgt_gen = (make_arg(size) for size in scalar_sizes)
    idx_gen = (make_idx(size, high=1) for size in scalar_sizes)
    src_gen = (make_arg(size) for size in scalar_sizes)
    for tgt, idx, src, acc in product(tgt_gen, idx_gen, src_gen, (True, False)):
        yield SampleInput(input=tgt.clone().requires_grad_(requires_grad),
                          args=(idx.clone(),
                                src.clone().requires_grad_(requires_grad),
                                acc))

    # Empty cases
    tgt_sizes = [(0,), (), (1,), (3, 2)]
    tgt_gen = (make_arg(size) for size in tgt_sizes)
    idx = make_idx((0,), high=1)
    src = make_arg((0,))
    for tgt, acc in product(tgt_gen, (True, False)):
        yield SampleInput(input=tgt.clone().requires_grad_(requires_grad),
                          args=(idx.clone(),
                                src.clone().requires_grad_(requires_grad),
                                acc))