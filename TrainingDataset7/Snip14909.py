def _get_weekday(self, date):
        """
        Return the weekday for a given date.

        The first day according to the week format is 0 and the last day is 6.
        """
        week_format = self.get_week_format()
        if week_format in {"%W", "%V"}:  # week starts on Monday
            return date.weekday()
        elif week_format == "%U":  # week starts on Sunday
            return (date.weekday() + 1) % 7
        else:
            raise ValueError("unknown week format: %s" % week_format)