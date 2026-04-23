def convert_to_tensor(x, dtype=None, sparse=None, ragged=None):
    if sparse:
        raise ValueError("`sparse=True` is not supported with torch backend")
    if ragged:
        raise ValueError("`ragged=True` is not supported with torch backend")
    if isinstance(x, Variable) or is_tensor(x):
        if isinstance(x, Variable):
            x = x.value
        device = get_device()
        if x.device != device:
            if x.is_meta:
                x = torch.empty_like(x, device=device)
            else:
                x = x.to(device)
        if dtype is not None:
            x = x.to(to_torch_dtype(dtype))
        return x
    if dtype is None:
        if isinstance(x, bool):
            return torch.as_tensor(x, dtype=torch.bool, device=get_device())
        elif isinstance(x, int):
            if x < -(2**31) or x >= 2**31:
                return torch.as_tensor(
                    x, dtype=torch.int64, device=get_device()
                )
            return torch.as_tensor(x, dtype=torch.int32, device=get_device())
        elif isinstance(x, float):
            return torch.as_tensor(
                x, dtype=to_torch_dtype(floatx()), device=get_device()
            )

    # Convert to np in case of any array-like that is not list or tuple.
    if not isinstance(x, (list, tuple)):
        x = np.array(x)
    elif len(x) > 0 and any(isinstance(x1, torch.Tensor) for x1 in x):
        # Handle list or tuple of torch tensors
        return torch.stack([convert_to_tensor(x1) for x1 in x])
    if isinstance(x, np.ndarray):
        if x.dtype == np.uint32:
            # Torch backend does not support uint32.
            x = x.astype(np.int64)
        if standardize_dtype(x.dtype) == "bfloat16":
            # Torch backend does not support converting bfloat16 ndarray.
            x = x.astype(np.float32)
            dtype = "bfloat16"
        dtype = dtype or x.dtype
    if dtype is None:
        dtype = result_type(
            *[getattr(item, "dtype", type(item)) for item in tree.flatten(x)]
        )
    dtype = to_torch_dtype(dtype)
    return torch.as_tensor(x, dtype=dtype, device=get_device())