def _is_lazy_cls(cls: type) -> bool | None:
    if (
        _issubclass_fast(cls, "numpy", "ndarray")
        or _issubclass_fast(cls, "numpy", "generic")
        or _issubclass_fast(cls, "cupy", "ndarray")
        or _issubclass_fast(cls, "torch", "Tensor")
        or _issubclass_fast(cls, "sparse", "SparseArray")
    ):
        return False
    if (
        _issubclass_fast(cls, "jax", "Array")
        or _issubclass_fast(cls, "jax.core", "Tracer")  # see is_jax_array for limitations
        or _issubclass_fast(cls, "dask.array", "Array")
        or _issubclass_fast(cls, "ndonnx", "Array")
    ):
        return True
    return  None