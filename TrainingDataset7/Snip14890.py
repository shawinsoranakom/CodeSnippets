def _get_current_year(self, date):
        """Return the start date of the current interval."""
        return date.replace(month=1, day=1)