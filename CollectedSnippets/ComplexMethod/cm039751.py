def _is_array_api_cls(cls: type) -> bool:
    return (
        # TODO: drop support for numpy<2 which didn't have __array_namespace__
        _issubclass_fast(cls, "numpy", "ndarray")
        or _issubclass_fast(cls, "numpy", "generic")
        or _issubclass_fast(cls, "cupy", "ndarray")
        or _issubclass_fast(cls, "torch", "Tensor")
        or _issubclass_fast(cls, "dask.array", "Array")
        or _issubclass_fast(cls, "sparse", "SparseArray")
        # TODO: drop support for jax<0.4.32 which didn't have __array_namespace__
        or _issubclass_fast(cls, "jax", "Array")
        or _issubclass_fast(cls, "jax.core", "Tracer")  # see is_jax_array for limitations
    )