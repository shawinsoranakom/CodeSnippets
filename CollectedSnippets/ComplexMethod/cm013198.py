def sample_inputs_logspace(op, device, dtype, requires_grad, **kwargs):
    ends = (-3, 0, 1.2, 2, 4)
    starts = (-2., 0, 1, 2, 4.3)
    nsteps = (0, 1, 2, 4)
    bases = (2., 1.1) if dtype in (torch.int8, torch.uint8) else (None, 2., 3., 1.1, 5.)
    for start, end, nstep, base in product(starts, ends, nsteps, bases):
        if dtype == torch.uint8 and end < 0 or start < 0:
            continue
        if nstep == 1 and isinstance(start, float) and not (dtype.is_complex or dtype.is_floating_point):
            # https://github.com/pytorch/pytorch/issues/82242
            continue
        if base is None:
            yield SampleInput(start, args=(end, nstep), kwargs={"dtype": dtype, "device": device})
        else:
            yield SampleInput(start, args=(end, nstep, base), kwargs={"dtype": dtype, "device": device})

    yield SampleInput(1, args=(3, 1, 2.))