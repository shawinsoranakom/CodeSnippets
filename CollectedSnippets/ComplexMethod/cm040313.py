def linspace(
    start, stop, num=50, endpoint=True, retstep=False, dtype=None, axis=0
):
    if axis != 0:
        raise ValueError(
            "torch.linspace does not support an `axis` argument. "
            f"Received axis={axis}"
        )
    if dtype is None:
        dtypes_to_resolve = [
            getattr(start, "dtype", type(start)),
            getattr(stop, "dtype", type(stop)),
            float,
        ]
        dtype = dtypes.result_type(*dtypes_to_resolve)
    dtype = to_torch_dtype(dtype)

    step = convert_to_tensor(torch.nan)
    if endpoint:
        if num > 1:
            step = (stop - start) / (num - 1)
    else:
        if num > 0:
            step = (stop - start) / num
        if num > 1:
            stop = stop - ((stop - start) / num)
    if hasattr(start, "__len__") and hasattr(stop, "__len__"):
        start = convert_to_tensor(start, dtype=dtype)
        stop = convert_to_tensor(stop, dtype=dtype)
        steps = torch.arange(num, dtype=dtype, device=get_device()) / (num - 1)

        # reshape `steps` to allow for broadcasting
        for i in range(start.ndim):
            steps = steps.unsqueeze(-1)

        # increments from `start` to `stop` in each dimension
        linspace = start[None] + steps * (stop - start)[None]
    else:
        linspace = torch.linspace(
            start=start,
            end=stop,
            steps=num,
            dtype=dtype,
            device=get_device(),
        )
    if retstep is True:
        return (linspace, step)
    return linspace