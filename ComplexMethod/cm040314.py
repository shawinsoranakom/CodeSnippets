def logspace(start, stop, num=50, endpoint=True, base=10, dtype=None, axis=0):
    if axis != 0:
        raise ValueError(
            "torch.logspace does not support an `axis` argument. "
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

    if endpoint is False:
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
        logspace = base**linspace
    else:
        compute_dtype = dtype
        # TODO: torch.logspace doesn't support float16 with cpu
        if get_device() == "cpu" and dtype == torch.float16:
            compute_dtype = torch.float32
        logspace = cast(
            torch.logspace(
                start=start,
                end=stop,
                steps=num,
                base=base,
                dtype=compute_dtype,
                device=get_device(),
            ),
            dtype,
        )
    return logspace