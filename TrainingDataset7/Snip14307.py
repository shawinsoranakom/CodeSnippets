def Z(self):
        """
        Time zone offset in seconds (i.e. '-43200' to '43200'). The offset for
        timezones west of UTC is always negative, and for those east of UTC is
        always positive.

        If timezone information is not available, return an empty string.
        """
        if self.timezone is None:
            return ""

        offset = self.timezone.utcoffset(self.data)

        # `offset` is a datetime.timedelta. For negative values (to the west of
        # UTC) only days can be negative (days=-1) and seconds are always
        # positive.
        # e.g.: UTC-1 -> timedelta(days=-1, seconds=82800, microseconds=0)
        # Positive offsets have days=0
        return offset.days * 86400 + offset.seconds