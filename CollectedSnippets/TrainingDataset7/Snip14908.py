def _get_current_week(self, date):
        """Return the start date of the current interval."""
        return date - datetime.timedelta(self._get_weekday(date))