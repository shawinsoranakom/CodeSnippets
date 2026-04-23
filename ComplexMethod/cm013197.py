def sample_inputs_linspace_tensor_overload(op, device, dtype, requires_grad, **kwargs):
    ends = (-3, 0, 1, 4, 50)
    starts = (-2., 0, 4.3, 50)
    nsteps = (0, 1, 50)
    is_start_end_tensors = ((True, True), (True, False), (False, True))
    make_arg = partial(torch.tensor, device=device, requires_grad=False)

    # Extra case to replicate off-by-one issue on CUDA
    cases = list(product(starts, ends, nsteps, is_start_end_tensors)) + [(0, 7, 50, (True, True))]
    for start, end, nstep, (is_start_tensor, is_end_tensor) in cases:
        if dtype == torch.uint8 and (end < 0 or start < 0):
            continue

        tensor_options = {"dtype": dtype, "device": device}
        if is_start_tensor:
            start = make_arg(start, dtype=torch.float32 if isinstance(start, float) else torch.int64)
        if is_end_tensor:
            end = make_arg(end, dtype=torch.float32 if isinstance(end, float) else torch.int64)

        yield SampleInput(start, args=(end, nstep), kwargs=tensor_options)

    yield SampleInput(1, args=(3, 1))