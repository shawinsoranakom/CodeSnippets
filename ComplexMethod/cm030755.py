def dst(self, dt):
        if dt is None or dt.tzinfo is None:
            # An exception instead may be sensible here, in one or more of
            # the cases.
            return ZERO
        assert dt.tzinfo is self

        # Find first Sunday in April.
        start = first_sunday_on_or_after(DSTSTART.replace(year=dt.year))
        assert start.weekday() == 6 and start.month == 4 and start.day <= 7

        # Find last Sunday in October.
        end = first_sunday_on_or_after(DSTEND.replace(year=dt.year))
        assert end.weekday() == 6 and end.month == 10 and end.day >= 25

        # Can't compare naive to aware objects, so strip the timezone from
        # dt first.
        dt = dt.replace(tzinfo=None)
        if start + HOUR <= dt < end:
            # DST is in effect.
            return HOUR
        elif end <= dt < end + HOUR:
            # Fold (an ambiguous hour): use dt.fold to disambiguate.
            return ZERO if dt.fold else HOUR
        elif start <= dt < start + HOUR:
            # Gap (a non-existent hour): reverse the fold rule.
            return HOUR if dt.fold else ZERO
        else:
            # DST is off.
            return ZERO