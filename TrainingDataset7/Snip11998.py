def _filter_or_exclude_inplace(self, negate, args, kwargs):
        if invalid_kwargs := PROHIBITED_FILTER_KWARGS.intersection(kwargs):
            invalid_kwargs_str = ", ".join(f"'{k}'" for k in sorted(invalid_kwargs))
            raise TypeError(f"The following kwargs are invalid: {invalid_kwargs_str}")
        if negate:
            self._query.add_q(~Q(*args, **kwargs))
        else:
            self._query.add_q(Q(*args, **kwargs))