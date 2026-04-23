def cast_to(weight, dtype=None, device=None, non_blocking=False, copy=False, stream=None, r=None):
    if device is None or weight.device == device:
        if not copy:
            if dtype is None or weight.dtype == dtype:
                return weight
        if stream is not None:
            wf_context = stream
            if hasattr(wf_context, "as_context"):
                wf_context = wf_context.as_context(stream)
            with wf_context:
                return weight.to(dtype=dtype, copy=copy)
        return weight.to(dtype=dtype, copy=copy)


    if stream is not None:
        wf_context = stream
        if hasattr(wf_context, "as_context"):
            wf_context = wf_context.as_context(stream)
        with wf_context:
            if r is None:
                r = torch.empty_like(weight, dtype=dtype, device=device)
            r.copy_(weight, non_blocking=non_blocking)
    else:
        if r is None:
            r = torch.empty_like(weight, dtype=dtype, device=device)
        r.copy_(weight, non_blocking=non_blocking)
    return r