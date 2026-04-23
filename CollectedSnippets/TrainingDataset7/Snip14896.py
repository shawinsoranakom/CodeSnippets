def _get_current_month(self, date):
        """Return the start date of the previous interval."""
        return date.replace(day=1)