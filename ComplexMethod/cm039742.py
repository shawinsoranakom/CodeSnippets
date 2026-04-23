def arange(start: float,
           /,
           stop: float | None = None,
           step: float = 1,
           *,
           dtype: DType | None = None,
           device: Device | None = None,
           **kwargs: object) -> Array:
    if stop is None:
        start, stop = 0, start
    if step > 0 and stop <= start or step < 0 and stop >= start:
        if dtype is None:
            if _builtin_all(isinstance(i, int) for i in [start, stop, step]):
                dtype = torch.int64
            else:
                dtype = torch.float32
        return torch.empty(0, dtype=dtype, device=device, **kwargs)
    return torch.arange(start, stop, step, dtype=dtype, device=device, **kwargs)