def fmean(data, weights=None):
    """Convert data to floats and compute the arithmetic mean.

    This runs faster than the mean() function and it always returns a float.
    If the input dataset is empty, it raises a StatisticsError.

    >>> fmean([3.5, 4.0, 5.25])
    4.25

    """
    if weights is None:

        try:
            n = len(data)
        except TypeError:
            # Handle iterators that do not define __len__().
            counter = count(1)
            total = fsum(compress(data, counter))
            n = next(counter) - 1
        else:
            total = fsum(data)

        if not n:
            raise StatisticsError('fmean requires at least one data point')

        return total / n

    if not isinstance(weights, (list, tuple)):
        weights = list(weights)

    try:
        num = sumprod(data, weights)
    except ValueError:
        raise StatisticsError('data and weights must be the same length')

    den = fsum(weights)

    if not den:
        raise StatisticsError('sum of weights must be non-zero')

    return num / den