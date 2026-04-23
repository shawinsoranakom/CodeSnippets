def _array_indexing(array, key, key_dtype, axis):
    """Index an array or scipy.sparse consistently across NumPy version."""
    xp, is_array_api, device_ = get_namespace_and_device(array)
    if is_array_api:
        if hasattr(key, "shape"):
            key = move_to(key, xp=xp, device=device_)
        elif isinstance(key, (int, slice)):
            # Passthrough for valid __getitem__ inputs as noted in the array
            # API spec.
            pass
        else:
            key = xp.asarray(key, device=device_)

        if hasattr(key, "dtype"):
            if xp.isdtype(key.dtype, "integral"):
                return xp.take(array, key, axis=axis)
            elif xp.isdtype(key.dtype, "bool"):
                # Array API does not support boolean indexing for n-dim arrays
                # yet hence the need to turn to equivalent integer indexing.
                indices = xp.arange(array.shape[axis], device=device_)
                return xp.take(array, indices[key], axis=axis)

    if issparse(array):
        if key_dtype == "bool":
            key = np.asarray(key)
        elif SCIPY_VERSION_BELOW_1_12:
            if isinstance(key, numbers.Integral):
                key = [key]
    if isinstance(key, tuple):
        key = list(key)
    return array[key, ...] if axis == 0 else array[:, key]