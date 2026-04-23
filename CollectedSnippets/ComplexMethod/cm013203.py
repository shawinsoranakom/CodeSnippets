def error_inputs_aminmax_amax_amin(op_info, device, is_ref=False, **kwargs):

    # Error Inputs for zero-dim tensors, when 'dim' arg is not provided.
    shape = (S, 0, S)
    err_msg_amax_amin = "reduction"
    err_msg_aminmax = "cannot compute aminmax over an empty dimension as the operation has no identity"
    if op_info.name in ['amax', 'amin', '_refs.amax', '_refs.amin']:
        yield ErrorInput(SampleInput(torch.rand(shape, device=device)), error_regex=err_msg_amax_amin)
    elif op_info.name == 'aminmax':
        yield ErrorInput(SampleInput(torch.rand(shape, device=device)), error_regex=err_msg_aminmax)

    # Error Inputs for tensors with more than 64 dimension
    sizes = [1] * 65
    err_msg1 = "only tensors with up to 64 dims are supported"
    yield ErrorInput(SampleInput(torch.randn(sizes, device=device), kwargs={'dim': -1}),
                     error_regex=err_msg1)
    yield ErrorInput(SampleInput(torch.randn(sizes, device=device), kwargs={'dim': 64}),
                     error_regex=err_msg1)

    # Error Inputs for repeated 'dim'
    if op_info.name in ['amax', 'amin', '_refs.amax', '_refs.amin']:
        dims = [(0, 0), (0, -4)]
        err_msg2 = "in the list of dims"
        x = torch.randn(S, S, S, S, device=device)
        for dim in dims:
            yield ErrorInput(SampleInput(x, kwargs={'dim': dim}), error_regex=err_msg2)

    # Error Input for illegal dtype
    input5 = torch.randn(L, L, dtype=torch.float32, device=device)
    max_values = torch.empty(L, dtype=torch.float32, device=device)
    min_values = torch.empty(L, dtype=torch.double, device=device)
    illegal_values = torch.empty(L, dtype=torch.int, device=device)

    # Unlike regular PyTorch, amax and amin refs don't require input and out
    # dtypes to match exactly:
    # https://github.com/pytorch/pytorch/pull/87765#pullrequestreview-1162023824
    if is_ref:
        err_msg_amax_amin2 = ("Attempting to cast from torch.float32 to out tensor with dtype "
                              "torch.int32, but this can't be cast because it is not safe!")
    else:
        err_msg_amax_amin2 = ("Expected the dtype for input and out to match, but got Float "
                              "for input's dtype and Int for out's dtype.")
    err_msg_aminmax2 = "Expected out tensor to have dtype float, but got double instead"

    if op_info.name in ['amax', 'amin', '_refs.amax', '_refs.amin']:
        yield ErrorInput(SampleInput(input5, kwargs={'dim': 0, 'out': illegal_values}),
                         error_regex=err_msg_amax_amin2)
    elif op_info.name == 'aminmax':
        yield ErrorInput(SampleInput(input5, kwargs={'dim': 0, 'out': (max_values, min_values)}),
                         error_regex=err_msg_aminmax2)

    # Error Inputs for functions to raise an error on specified zero'd dimension as reduction dim
    err_msg3 = "reduction"
    # FIXME: eager and ref impl throw different types of errors
    error_type = IndexError if 'refs' not in op_info.name else RuntimeError
    yield ErrorInput(SampleInput(torch.rand(shape, device=device), kwargs={'dim': 1}),
                     error_type=error_type, error_regex=err_msg3)