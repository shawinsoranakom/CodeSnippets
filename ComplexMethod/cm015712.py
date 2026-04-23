def result_check(expected, got, ulp_tol=5, abs_tol=0.0):
    # Common logic of MathTests.(ftest, test_testcases, test_mtestcases)
    """Compare arguments expected and got, as floats, if either
    is a float, using a tolerance expressed in multiples of
    ulp(expected) or absolutely (if given and greater).

    As a convenience, when neither argument is a float, and for
    non-finite floats, exact equality is demanded. Also, nan==nan
    as far as this function is concerned.

    Returns None on success and an error message on failure.
    """

    # Check exactly equal (applies also to strings representing exceptions)
    if got == expected:
        if not got and not expected:
            if math.copysign(1, got) != math.copysign(1, expected):
                return f"expected {expected}, got {got} (zero has wrong sign)"
        return None

    failure = "not equal"

    # Turn mixed float and int comparison (e.g. floor()) to all-float
    if isinstance(expected, float) and isinstance(got, int):
        got = float(got)
    elif isinstance(got, float) and isinstance(expected, int):
        expected = float(expected)

    if isinstance(expected, float) and isinstance(got, float):
        if math.isnan(expected) and math.isnan(got):
            # Pass, since both nan
            failure = None
        elif math.isinf(expected) or math.isinf(got):
            # We already know they're not equal, drop through to failure
            pass
        else:
            # Both are finite floats (now). Are they close enough?
            failure = ulp_abs_check(expected, got, ulp_tol, abs_tol)

    # arguments are not equal, and if numeric, are too far apart
    if failure is not None:
        fail_fmt = "expected {!r}, got {!r}"
        fail_msg = fail_fmt.format(expected, got)
        fail_msg += ' ({})'.format(failure)
        return fail_msg
    else:
        return None