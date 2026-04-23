def _check_fix_default_value(self):
        """
        Warn that using an actual date or datetime value is probably wrong;
        it's only evaluated on server startup.
        """
        if not self.has_default():
            return []

        value = self.default
        if isinstance(value, datetime.datetime):
            now = None
        elif isinstance(value, datetime.time):
            now = _get_naive_now()
            # This will not use the right date in the race condition where now
            # is just before the date change and value is just past 0:00.
            value = datetime.datetime.combine(now.date(), value)
        else:
            # No explicit time / datetime value -- no checks necessary
            return []
        # At this point, value is a datetime object.
        return self._check_if_value_fixed(value, now=now)