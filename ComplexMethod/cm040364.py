def convert_to_tensor(x, dtype=None, sparse=None, ragged=None):
    if sparse:
        raise ValueError("`sparse=True` is not supported with numpy backend")
    if ragged:
        raise ValueError("`ragged=True` is not supported with numpy backend")
    if dtype is not None:
        dtype = standardize_dtype(dtype)
    if isinstance(x, Variable):
        if dtype and dtype != x.dtype:
            return x.value.astype(dtype)
        return x.value
    if not is_tensor(x) and standardize_dtype(dtype) == "bfloat16":
        # Can't create bfloat16 arrays on the fly (e.g. from a h5 Dataset).
        # Instead we convert "as is" (to stored dtype) and cast.
        return np.asarray(x).astype(dtype)
    if dtype is None:
        dtype = result_type(
            *[getattr(item, "dtype", type(item)) for item in tree.flatten(x)]
        )
    return np.array(x, dtype=dtype)