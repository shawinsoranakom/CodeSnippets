def linear_regression(x, y, /, *, proportional=False):
    """Slope and intercept for simple linear regression.

    Return the slope and intercept of simple linear regression
    parameters estimated using ordinary least squares. Simple linear
    regression describes relationship between an independent variable
    *x* and a dependent variable *y* in terms of a linear function:

        y = slope * x + intercept + noise

    where *slope* and *intercept* are the regression parameters that are
    estimated, and noise represents the variability of the data that was
    not explained by the linear regression (it is equal to the
    difference between predicted and actual values of the dependent
    variable).

    The parameters are returned as a named tuple.

    >>> x = [1, 2, 3, 4, 5]
    >>> noise = NormalDist().samples(5, seed=42)
    >>> y = [3 * x[i] + 2 + noise[i] for i in range(5)]
    >>> linear_regression(x, y)  #doctest: +ELLIPSIS
    LinearRegression(slope=3.17495..., intercept=1.00925...)

    If *proportional* is true, the independent variable *x* and the
    dependent variable *y* are assumed to be directly proportional.
    The data is fit to a line passing through the origin.

    Since the *intercept* will always be 0.0, the underlying linear
    function simplifies to:

        y = slope * x + noise

    >>> y = [3 * x[i] + noise[i] for i in range(5)]
    >>> linear_regression(x, y, proportional=True)  #doctest: +ELLIPSIS
    LinearRegression(slope=2.90475..., intercept=0.0)

    """
    # https://en.wikipedia.org/wiki/Simple_linear_regression
    n = len(x)
    if len(y) != n:
        raise StatisticsError('linear regression requires that both inputs have same number of data points')
    if n < 2:
        raise StatisticsError('linear regression requires at least two data points')

    if not proportional:
        xbar = fsum(x) / n
        ybar = fsum(y) / n
        x = [xi - xbar for xi in x]  # List because used three times below
        y = (yi - ybar for yi in y)  # Generator because only used once below

    sxy = sumprod(x, y) + 0.0        # Add zero to coerce result to a float
    sxx = sumprod(x, x)

    try:
        slope = sxy / sxx   # equivalent to:  covariance(x, y) / variance(x)
    except ZeroDivisionError:
        raise StatisticsError('x is constant')

    intercept = 0.0 if proportional else ybar - slope * xbar
    return LinearRegression(slope=slope, intercept=intercept)