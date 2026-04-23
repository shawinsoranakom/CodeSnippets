def move_to(*arrays, xp, device):
    """Move all arrays to `xp` and `device`.

    Each array will be moved to the reference namespace and device if
    it is not already using it. Otherwise the array is left unchanged.

    `arrays` may contain `None` entries, these are left unchanged.

    Sparse arrays are accepted (as pass through) if the reference namespace is
    NumPy, in which case they are returned unchanged. Otherwise a `TypeError`
    is raised.

    Parameters
    ----------
    *arrays : iterable of arrays
        Arrays to (potentially) move.

    xp : namespace
        Array API namespace to move arrays to.

    device : device
        Array API device to move arrays to.

    Returns
    -------
    arrays : tuple or array
        Tuple of arrays with the same namespace and device as reference. Single array
        returned if only one `arrays` input.
    """
    sparse_mask = [sp.issparse(array) for array in arrays]
    none_mask = [array is None for array in arrays]
    if any(sparse_mask) and not _is_numpy_namespace(xp):
        raise TypeError(
            "Sparse arrays are only accepted (and passed through) when the target "
            "namespace is Numpy"
        )

    arrays_ = arrays
    # Down cast float64 `arrays` when highest precision of `xp`/`device` is float32
    if _max_precision_float_dtype(xp, device) == xp.float32:
        arrays_ = []
        for array in arrays:
            xp_array, _ = get_namespace(array)
            if getattr(array, "dtype", None) == xp_array.float64:
                arrays_.append(xp_array.astype(array, xp_array.float32))
            else:
                arrays_.append(array)

    converted_arrays = []
    for array, is_sparse, is_none in zip(arrays_, sparse_mask, none_mask):
        if is_none:
            converted_arrays.append(None)
        elif is_sparse:
            converted_arrays.append(array)
        else:
            xp_array, _, device_array = get_namespace_and_device(array)
            if xp == xp_array and device == device_array:
                converted_arrays.append(array)
            else:
                try:
                    # The dlpack protocol is the future proof and library agnostic
                    # method to transfer arrays across namespace and device boundaries
                    # hence this method is attempted first and going through NumPy is
                    # only used as fallback in case of failure.
                    # Note: copy=None is the default since array-api 2023.12. Namespace
                    # libraries should only trigger a copy automatically if needed.
                    array_converted = xp.from_dlpack(array, device=device)
                    # `AttributeError` occurs when `__dlpack__` and `__dlpack_device__`
                    # methods are not present on the input array
                    # `TypeError` and `NotImplementedError` for packages that do not
                    # yet support dlpack 1.0
                    # (i.e. the `device`/`copy` kwargs, e.g., torch <= 2.8.0)
                    # See https://github.com/data-apis/array-api/pull/741 for
                    # more details about the introduction of the `copy` and `device`
                    # kwargs in the from_dlpack method and their expected
                    # meaning by namespaces implementing the array API spec.
                    # TODO: try removing this once DLPack v1 more widely supported
                    # TODO: ValueError not needed once min NumPy >=2.4.0:
                    # https://github.com/numpy/numpy/issues/30341
                except (
                    AttributeError,
                    TypeError,
                    NotImplementedError,
                    BufferError,
                    ValueError,
                ):
                    # Converting to numpy is tricky, handle this via dedicated function
                    if _is_numpy_namespace(xp):
                        array_converted = _convert_to_numpy(array, xp_array)
                    # Convert from numpy, all array libraries can do this
                    elif _is_numpy_namespace(xp_array):
                        array_converted = xp.asarray(array, device=device)
                    else:
                        # There is no generic way to convert from namespace A to B
                        # So we first convert from A to numpy and then from numpy to B
                        # The way to avoid this round trip is to lobby for DLpack
                        # support in libraries A and B
                        array_np = _convert_to_numpy(array, xp_array)
                        array_converted = xp.asarray(array_np, device=device)
                converted_arrays.append(array_converted)

    return (
        converted_arrays[0] if len(converted_arrays) == 1 else tuple(converted_arrays)
    )