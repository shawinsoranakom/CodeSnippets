def dst(self, when):
        if when is None or when.tzinfo is None:
            # An exception may be sensible here, in one or both cases.
            # It depends on how you want to treat them.  The default
            # fromutc() implementation (called by the default astimezone()
            # implementation) passes a datetime with when.tzinfo is self.
            return ZERO
        assert when.tzinfo is self
        start, end = us_dst_range(when.year)
        # Can't compare naive to aware objects, so strip the timezone from
        # when first.
        when = when.replace(tzinfo=None)
        if start + HOUR <= when < end - HOUR:
            # DST is in effect.
            return HOUR
        if end - HOUR <= when < end:
            # Fold (an ambiguous hour): use when.fold to disambiguate.
            return ZERO if when.fold else HOUR
        if start <= when < start + HOUR:
            # Gap (a non-existent hour): reverse the fold rule.
            return HOUR if when.fold else ZERO
        # DST is off.
        return ZERO