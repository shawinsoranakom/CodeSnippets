def _rhs_not_none_values(self, rhs):
        for x in rhs:
            if isinstance(x, (list, tuple)):
                yield from self._rhs_not_none_values(x)
            elif x is not None:
                yield True