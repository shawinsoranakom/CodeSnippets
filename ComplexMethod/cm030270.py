def correlation(x, y, /, *, method='linear'):
    """Pearson's correlation coefficient

    Return the Pearson's correlation coefficient for two inputs. Pearson's
    correlation coefficient *r* takes values between -1 and +1. It measures
    the strength and direction of a linear relationship.

    >>> x = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    >>> y = [9, 8, 7, 6, 5, 4, 3, 2, 1]
    >>> correlation(x, x)
    1.0
    >>> correlation(x, y)
    -1.0

    If *method* is "ranked", computes Spearman's rank correlation coefficient
    for two inputs.  The data is replaced by ranks.  Ties are averaged
    so that equal values receive the same rank.  The resulting coefficient
    measures the strength of a monotonic relationship.

    Spearman's rank correlation coefficient is appropriate for ordinal
    data or for continuous data that doesn't meet the linear proportion
    requirement for Pearson's correlation coefficient.

    """
    # https://en.wikipedia.org/wiki/Pearson_correlation_coefficient
    # https://en.wikipedia.org/wiki/Spearman%27s_rank_correlation_coefficient
    n = len(x)
    if len(y) != n:
        raise StatisticsError('correlation requires that both inputs have same number of data points')
    if n < 2:
        raise StatisticsError('correlation requires at least two data points')
    if method not in {'linear', 'ranked'}:
        raise ValueError(f'Unknown method: {method!r}')

    if method == 'ranked':
        start = (n - 1) / -2            # Center rankings around zero
        x = _rank(x, start=start)
        y = _rank(y, start=start)

    else:
        xbar = fsum(x) / n
        ybar = fsum(y) / n
        x = [xi - xbar for xi in x]
        y = [yi - ybar for yi in y]

    sxy = sumprod(x, y)
    sxx = sumprod(x, x)
    syy = sumprod(y, y)

    try:
        return sxy / _sqrtprod(sxx, syy)
    except ZeroDivisionError:
        raise StatisticsError('at least one of the inputs is constant')