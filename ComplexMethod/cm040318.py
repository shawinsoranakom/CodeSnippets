def prod(x, axis=None, keepdims=False, dtype=None):
    x = convert_to_tensor(x)
    if dtype is None:
        dtype = dtypes.result_type(x.dtype)
        if dtype == "bool":
            dtype = "int32"
        elif dtype in ("int8", "int16"):
            dtype = "int32"
        # TODO: torch.prod doesn't support uint32
        elif dtype == "uint8":
            dtype = "int32"
    compute_dtype = dtype
    # TODO: torch.prod doesn't support float16 with cpu
    if get_device() == "cpu" and compute_dtype == "float16":
        compute_dtype = "float32"
    if axis is None:
        return cast(torch.prod(x, dtype=to_torch_dtype(compute_dtype)), dtype)
    axis = to_tuple_or_list(axis)
    for a in axis:
        # `torch.prod` does not handle multiple axes.
        x = cast(
            torch.prod(
                x, dim=a, keepdim=keepdims, dtype=to_torch_dtype(compute_dtype)
            ),
            dtype,
        )
    return x