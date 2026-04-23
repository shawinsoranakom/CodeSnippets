def array_namespace(
    *xs: Array | complex | None,
    api_version: str | None = None,
    use_compat: bool | None = None,
) -> Namespace:
    """
    Get the array API compatible namespace for the arrays `xs`.

    Parameters
    ----------
    xs: arrays
        one or more arrays. xs can also be Python scalars (bool, int, float,
        complex, or None), which are ignored.

    api_version: str
        The newest version of the spec that you need support for (currently
        the compat library wrapped APIs support v2024.12).

    use_compat: bool or None
        If None (the default), the native namespace will be returned if it is
        already array API compatible, otherwise a compat wrapper is used. If
        True, the compat library wrapped library will be returned. If False,
        the native library namespace is returned.

    Returns
    -------

    out: namespace
        The array API compatible namespace corresponding to the arrays in `xs`.

    Raises
    ------
    TypeError
        If `xs` contains arrays from different array libraries or contains a
        non-array.


    Typical usage is to pass the arguments of a function to
    `array_namespace()` at the top of a function to get the corresponding
    array API namespace:

    .. code:: python

       def your_function(x, y):
           xp = array_api_compat.array_namespace(x, y)
           # Now use xp as the array library namespace
           return xp.mean(x, axis=0) + 2*xp.std(y, axis=0)


    Wrapped array namespaces can also be imported directly. For example,
    `array_namespace(np.array(...))` will return `array_api_compat.numpy`.
    This function will also work for any array library not wrapped by
    array-api-compat if it explicitly defines `__array_namespace__
    <https://data-apis.org/array-api/latest/API_specification/generated/array_api.array.__array_namespace__.html>`__
    (the wrapped namespace is always preferred if it exists).

    See Also
    --------

    is_array_api_obj
    is_numpy_array
    is_cupy_array
    is_torch_array
    is_dask_array
    is_jax_array
    is_pydata_sparse_array

    """
    namespaces: set[Namespace] = set()
    for x in xs:
        xp, info = _cls_to_namespace(cast(Hashable, type(x)), api_version, use_compat)
        if info is _ClsToXPInfo.SCALAR:
            continue

        if (
            info is _ClsToXPInfo.MAYBE_JAX_ZERO_GRADIENT
            and _is_jax_zero_gradient_array(x)
        ):
            xp = _jax_namespace(api_version, use_compat)

        if xp is None:
            get_ns = getattr(x, "__array_namespace__", None)
            if get_ns is None:
                raise TypeError(f"{type(x).__name__} is not a supported array type")
            if use_compat:
                raise ValueError(
                    "The given array does not have an array-api-compat wrapper"
                )
            xp = get_ns(api_version=api_version)

        namespaces.add(xp)

    try:
        (xp,) = namespaces
        return xp
    except ValueError:
        if not namespaces:
            raise TypeError(
                "array_namespace requires at least one non-scalar array input"
            )
        raise TypeError(f"Multiple namespaces for array inputs: {namespaces}")