def _merge(self, other: Intervals | Iterable[tuple[T, T, AbstractSet]], difference: bool) -> Intervals:
        """ Return the difference or intersection of two sets of intervals. """
        result = Intervals(keep_distinct=self._keep_distinct)
        append = result._items.append

        # using 'self' and 'other' below forces normalization
        bounds1 = _boundaries(self, 'start', 'stop')
        bounds2 = _boundaries(Intervals(other, keep_distinct=self._keep_distinct), 'switch', 'switch')

        start = None                    # set by start/stop
        recs1 = None                    # set by start
        enabled = difference            # changed by switch
        if self._keep_distinct:
            bounds = sorted(itertools.chain(bounds1, bounds2), key=lambda i: i[0])
        else:
            bounds = sorted(itertools.chain(bounds1, bounds2))
        for value, flag, recs in bounds:
            if flag == 'start':
                start = value
                recs1 = recs
            elif flag == 'stop':
                if enabled and start < value:
                    append((start, value, recs1))
                start = None
            else:
                if not enabled and start is not None:
                    start = value
                if enabled and start is not None and start < value:
                    append((start, value, recs1))
                enabled = not enabled

        return result