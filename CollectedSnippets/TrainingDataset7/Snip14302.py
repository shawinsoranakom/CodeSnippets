def O(self):  # NOQA: E743, E741
        """
        Difference to Greenwich time in hours; e.g. '+0200', '-0430'.

        If timezone information is not available, return an empty string.
        """
        if self.timezone is None:
            return ""

        offset = self.timezone.utcoffset(self.data)
        seconds = offset.days * 86400 + offset.seconds
        sign = "-" if seconds < 0 else "+"
        seconds = abs(seconds)
        return "%s%02d%02d" % (sign, seconds // 3600, (seconds // 60) % 60)