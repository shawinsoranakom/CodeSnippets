def cross(x1, x2, axisa=-1, axisb=-1, axisc=-1, axis=None):
    if axisa != -1 or axisb != -1 or axisc != -1:
        raise ValueError(
            "Torch backend does not support `axisa`, `axisb`, or `axisc`. "
            f"Received: axisa={axisa}, axisb={axisb}, axisc={axisc}. Please "
            "use `axis` arg in torch backend."
        )
    x1 = convert_to_tensor(x1)
    x2 = convert_to_tensor(x2)
    compute_dtype = dtypes.result_type(x1.dtype, x2.dtype)
    result_dtype = compute_dtype
    # TODO: torch.cross doesn't support bfloat16 with gpu
    if get_device() == "cuda" and compute_dtype == "bfloat16":
        compute_dtype = "float32"
    # TODO: torch.cross doesn't support float16 with cpu
    elif get_device() == "cpu" and compute_dtype == "float16":
        compute_dtype = "float32"
    x1 = cast(x1, compute_dtype)
    x2 = cast(x2, compute_dtype)
    return cast(torch.cross(x1, x2, dim=axis), result_dtype)