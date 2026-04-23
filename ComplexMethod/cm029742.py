def choices(self, population, weights=None, *, cum_weights=None, k=1):
        """Return a k sized list of population elements chosen with replacement.

        If the relative weights or cumulative weights are not specified,
        the selections are made with equal probability.

        """
        random = self.random
        n = len(population)
        if cum_weights is None:
            if weights is None:
                floor = _floor
                n += 0.0    # convert to float for a small speed improvement
                return [population[floor(random() * n)] for i in _repeat(None, k)]
            try:
                cum_weights = list(_accumulate(weights))
            except TypeError:
                if not isinstance(weights, int):
                    raise
                k = weights
                raise TypeError(
                    f'The number of choices must be a keyword argument: {k=}'
                ) from None
        elif weights is not None:
            raise TypeError('Cannot specify both weights and cumulative weights')
        if len(cum_weights) != n:
            raise ValueError('The number of weights does not match the population')
        total = cum_weights[-1] + 0.0   # convert to float
        if total <= 0.0:
            raise ValueError('Total of weights must be greater than zero')
        if not _isfinite(total):
            raise ValueError('Total of weights must be finite')
        bisect = _bisect
        hi = n - 1
        return [population[bisect(cum_weights, random() * total, 0, hi)]
                for i in _repeat(None, k)]