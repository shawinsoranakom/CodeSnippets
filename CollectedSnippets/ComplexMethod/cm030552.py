def approx_equal(x, y, tol=1e-12, rel=1e-7):
    """approx_equal(x, y [, tol [, rel]]) => True|False

    Return True if numbers x and y are approximately equal, to within some
    margin of error, otherwise return False. Numbers which compare equal
    will also compare approximately equal.

    x is approximately equal to y if the difference between them is less than
    an absolute error tol or a relative error rel, whichever is bigger.

    If given, both tol and rel must be finite, non-negative numbers. If not
    given, default values are tol=1e-12 and rel=1e-7.

    >>> approx_equal(1.2589, 1.2587, tol=0.0003, rel=0)
    True
    >>> approx_equal(1.2589, 1.2587, tol=0.0001, rel=0)
    False

    Absolute error is defined as abs(x-y); if that is less than or equal to
    tol, x and y are considered approximately equal.

    Relative error is defined as abs((x-y)/x) or abs((x-y)/y), whichever is
    smaller, provided x or y are not zero. If that figure is less than or
    equal to rel, x and y are considered approximately equal.

    Complex numbers are not directly supported. If you wish to compare to
    complex numbers, extract their real and imaginary parts and compare them
    individually.

    NANs always compare unequal, even with themselves. Infinities compare
    approximately equal if they have the same sign (both positive or both
    negative). Infinities with different signs compare unequal; so do
    comparisons of infinities with finite numbers.
    """
    if tol < 0 or rel < 0:
        raise ValueError('error tolerances must be non-negative')
    # NANs are never equal to anything, approximately or otherwise.
    if math.isnan(x) or math.isnan(y):
        return False
    # Numbers which compare equal also compare approximately equal.
    if x == y:
        # This includes the case of two infinities with the same sign.
        return True
    if math.isinf(x) or math.isinf(y):
        # This includes the case of two infinities of opposite sign, or
        # one infinity and one finite number.
        return False
    # Two finite numbers.
    actual_error = abs(x - y)
    allowed_error = max(tol, rel*max(abs(x), abs(y)))
    return actual_error <= allowed_error