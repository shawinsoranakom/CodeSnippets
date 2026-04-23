def __getitem__(self, k):
        """Retrieve an item or slice from the set of results."""
        if not isinstance(k, (int, slice)):
            raise TypeError(
                "QuerySet indices must be integers or slices, not %s."
                % type(k).__name__
            )
        if (isinstance(k, int) and k < 0) or (
            isinstance(k, slice)
            and (
                (k.start is not None and k.start < 0)
                or (k.stop is not None and k.stop < 0)
            )
        ):
            raise ValueError("Negative indexing is not supported.")

        if self._result_cache is not None:
            return self._result_cache[k]

        if isinstance(k, slice):
            qs = self._chain()
            if k.start is not None:
                start = int(k.start)
            else:
                start = None
            if k.stop is not None:
                stop = int(k.stop)
            else:
                stop = None
            qs.query.set_limits(start, stop)
            return list(qs)[:: k.step] if k.step else qs

        qs = self._chain()
        qs.query.set_limits(k, k + 1)
        qs._fetch_all()
        return qs._result_cache[0]