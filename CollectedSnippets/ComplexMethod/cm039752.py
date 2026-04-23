def _cls_to_namespace(
    cls: type,
    api_version: str | None,
    use_compat: bool | None,
) -> tuple[Namespace | None, _ClsToXPInfo | None]:
    if use_compat not in (None, True, False):
        raise ValueError("use_compat must be None, True, or False")
    _use_compat = use_compat in (None, True)
    cls_ = cast(Hashable, cls)  # Make mypy happy

    if (
        _issubclass_fast(cls_, "numpy", "ndarray") 
        or _issubclass_fast(cls_, "numpy", "generic")
    ):
        if use_compat is True:
            _check_api_version(api_version)
            from .. import numpy as xp
        elif use_compat is False:
            import numpy as xp  # type: ignore[no-redef]
        else:
            # NumPy 2.0+ have __array_namespace__; however they are not
            # yet fully array API compatible.
            from .. import numpy as xp  # type: ignore[no-redef]
        return xp, _ClsToXPInfo.MAYBE_JAX_ZERO_GRADIENT

    # Note: this must happen _after_ the test for np.generic,
    # because np.float64 and np.complex128 are subclasses of float and complex.
    if issubclass(cls, int | float | complex | type(None)):
        return None, _ClsToXPInfo.SCALAR

    if _issubclass_fast(cls_, "cupy", "ndarray"):
        if _use_compat:
            _check_api_version(api_version)
            from .. import cupy as xp  # type: ignore[no-redef]
        else:
            import cupy as xp  # type: ignore[no-redef]
        return xp, None

    if _issubclass_fast(cls_, "torch", "Tensor"):
        if _use_compat:
            _check_api_version(api_version)
            from .. import torch as xp  # type: ignore[no-redef]
        else:
            import torch as xp  # type: ignore[no-redef]
        return xp, None

    if _issubclass_fast(cls_, "dask.array", "Array"):
        if _use_compat:
            _check_api_version(api_version)
            from ..dask import array as xp  # type: ignore[no-redef]
        else:
            import dask.array as xp  # type: ignore[no-redef]
        return xp, None

    # Backwards compatibility for jax<0.4.32
    if _issubclass_fast(cls_, "jax", "Array"):
        return _jax_namespace(api_version, use_compat), None

    return None, None