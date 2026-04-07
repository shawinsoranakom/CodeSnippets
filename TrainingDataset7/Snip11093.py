def _check_fix_default_value(self):
        """
        Warn that using an actual date or datetime value is probably wrong;
        it's only evaluated on server startup.
        """
        if not self.has_default():
            return []

        value = self.default
        if isinstance(value, datetime.datetime):
            value = _to_naive(value).date()
        elif isinstance(value, datetime.date):
            pass
        else:
            # No explicit date / datetime value -- no checks necessary
            return []
        # At this point, value is a date object.
        return self._check_if_value_fixed(value)