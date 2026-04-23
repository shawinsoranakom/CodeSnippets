def assert_equal(actual, desired, err_msg="", verbose=True):
    """
    Raises an AssertionError if two objects are not equal.

    Given two objects (scalars, lists, tuples, dictionaries or numpy arrays),
    check that all elements of these objects are equal. An exception is raised
    at the first conflicting values.

    When one of `actual` and `desired` is a scalar and the other is array_like,
    the function checks that each element of the array_like object is equal to
    the scalar.

    This function handles NaN comparisons as if NaN was a "normal" number.
    That is, AssertionError is not raised if both objects have NaNs in the same
    positions.  This is in contrast to the IEEE standard on NaNs, which says
    that NaN compared to anything must return False.

    Parameters
    ----------
    actual : array_like
        The object to check.
    desired : array_like
        The expected object.
    err_msg : str, optional
        The error message to be printed in case of failure.
    verbose : bool, optional
        If True, the conflicting values are appended to the error message.

    Raises
    ------
    AssertionError
        If actual and desired are not equal.

    Examples
    --------
    >>> np.testing.assert_equal([4, 5], [4, 6])
    Traceback (most recent call last):
        ...
    AssertionError:
    Items are not equal:
    item=1
     ACTUAL: 5
     DESIRED: 6

    The following comparison does not raise an exception.  There are NaNs
    in the inputs, but they are in the same positions.

    >>> np.testing.assert_equal(np.array([1.0, 2.0, np.nan]), [1, 2, np.nan])

    """
    __tracebackhide__ = True  # Hide traceback for py.test

    num_nones = sum([actual is None, desired is None])
    if num_nones == 1:
        raise AssertionError(f"Not equal: {actual} != {desired}")
    elif num_nones == 2:
        return True
    # else, carry on

    if isinstance(actual, np.DType) or isinstance(desired, np.DType):
        result = actual == desired
        if not result:
            raise AssertionError(f"Not equal: {actual} != {desired}")
        else:
            return True

    if isinstance(desired, str) and isinstance(actual, str):
        if actual != desired:
            raise AssertionError(f"Strings not equal: {actual!r} != {desired!r}")
        return

    if isinstance(desired, dict):
        if not isinstance(actual, dict):
            raise AssertionError(repr(type(actual)))
        assert_equal(len(actual), len(desired), err_msg, verbose)
        for k in desired:
            if k not in actual:
                raise AssertionError(repr(k))
            assert_equal(actual[k], desired[k], f"key={k!r}\n{err_msg}", verbose)
        return
    if isinstance(desired, (list, tuple)) and isinstance(actual, (list, tuple)):
        assert_equal(len(actual), len(desired), err_msg, verbose)
        for k in range(len(desired)):
            assert_equal(actual[k], desired[k], f"item={k!r}\n{err_msg}", verbose)
        return

    from torch._numpy import imag, iscomplexobj, isscalar, ndarray, real, signbit

    if isinstance(actual, ndarray) or isinstance(desired, ndarray):
        return assert_array_equal(actual, desired, err_msg, verbose)
    msg = build_err_msg([actual, desired], err_msg, verbose=verbose)

    # Handle complex numbers: separate into real/imag to handle
    # nan/inf/negative zero correctly
    # XXX: catch ValueError for subclasses of ndarray where iscomplex fail
    try:
        usecomplex = iscomplexobj(actual) or iscomplexobj(desired)
    except (ValueError, TypeError):
        usecomplex = False

    if usecomplex:
        if iscomplexobj(actual):
            actualr = real(actual)
            actuali = imag(actual)
        else:
            actualr = actual
            actuali = 0
        if iscomplexobj(desired):
            desiredr = real(desired)
            desiredi = imag(desired)
        else:
            desiredr = desired
            desiredi = 0
        try:
            assert_equal(actualr, desiredr)
            assert_equal(actuali, desiredi)
        except AssertionError:
            raise AssertionError(msg)  # noqa: B904

    # isscalar test to check cases such as [np.nan] != np.nan
    if isscalar(desired) != isscalar(actual):
        raise AssertionError(msg)

    # Inf/nan/negative zero handling
    try:
        isdesnan = gisnan(desired)
        isactnan = gisnan(actual)
        if isdesnan and isactnan:
            return  # both nan, so equal

        if desired == 0 and actual == 0:
            if not signbit(desired) == signbit(actual):
                raise AssertionError(msg)

    except (TypeError, ValueError, NotImplementedError):
        pass

    try:
        # Explicitly use __eq__ for comparison, gh-2552
        if not (desired == actual):
            raise AssertionError(msg)

    except (DeprecationWarning, FutureWarning) as e:
        # this handles the case when the two types are not even comparable
        if "elementwise == comparison" in e.args[0]:
            raise AssertionError(msg)  # noqa: B904
        else:
            raise