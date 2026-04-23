def _check_ns_shape_dtype(
    actual: Array,
    desired: Array,
    check_dtype: bool,
    check_shape: bool,
    check_scalar: bool,
) -> ModuleType:  # numpydoc ignore=RT03
    """
    Assert that namespace, shape and dtype of the two arrays match.

    Parameters
    ----------
    actual : Array
        The array produced by the tested function.
    desired : Array
        The expected array (typically hardcoded).
    check_dtype, check_shape : bool, default: True
        Whether to check agreement between actual and desired dtypes and shapes
    check_scalar : bool, default: False
        NumPy only: whether to check agreement between actual and desired types -
        0d array vs scalar.

    Returns
    -------
    Arrays namespace.
    """
    actual_xp = array_namespace(actual)  # Raises on scalars and lists
    desired_xp = array_namespace(desired)

    msg = f"namespaces do not match: {actual_xp} != f{desired_xp}"
    assert actual_xp == desired_xp, msg

    # Dask uses nan instead of None for unknown shapes
    actual_shape = cast(tuple[float, ...], actual.shape)
    desired_shape = cast(tuple[float, ...], desired.shape)
    assert None not in actual_shape  # Requires explicit support
    assert None not in desired_shape
    if is_dask_namespace(desired_xp):
        if any(math.isnan(i) for i in actual_shape):
            actual_shape = actual.compute().shape  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
        if any(math.isnan(i) for i in desired_shape):
            desired_shape = desired.compute().shape  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]

    if check_shape:
        msg = f"shapes do not match: {actual_shape} != f{desired_shape}"
        assert actual_shape == desired_shape, msg
    else:
        # Ignore shape, but check flattened size. This is normally done by
        # np.testing.assert_array_equal etc even when strict=False, but not for
        # non-materializable arrays.
        actual_size = math.prod(actual_shape)  # pyright: ignore[reportUnknownArgumentType]
        desired_size = math.prod(desired_shape)  # pyright: ignore[reportUnknownArgumentType]
        msg = f"sizes do not match: {actual_size} != f{desired_size}"
        assert actual_size == desired_size, msg

    if check_dtype:
        msg = f"dtypes do not match: {actual.dtype} != {desired.dtype}"
        assert actual.dtype == desired.dtype, msg

    if is_numpy_namespace(actual_xp) and check_scalar:
        # only NumPy distinguishes between scalars and arrays; we do if check_scalar.
        _msg = (
            "array-ness does not match:\n Actual: "
            f"{type(actual)}\n Desired: {type(desired)}"
        )
        assert np.isscalar(actual) == np.isscalar(desired), _msg

    return desired_xp