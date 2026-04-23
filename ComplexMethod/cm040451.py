def standardize_dtype(dtype):
    if dtype is None:
        return config.floatx()
    dtype = dtypes.PYTHON_DTYPES_MAP.get(dtype, dtype)
    if hasattr(dtype, "name"):
        dtype = dtype.name
    elif hasattr(dtype, "__name__"):
        dtype = dtype.__name__
    elif hasattr(dtype, "__str__") and (
        "torch" in str(dtype) or "jax.numpy" in str(dtype)
    ):
        dtype = str(dtype).split(".")[-1]

    if dtype not in dtypes.ALLOWED_DTYPES:
        raise ValueError(f"Invalid dtype: {dtype}")
    return dtype