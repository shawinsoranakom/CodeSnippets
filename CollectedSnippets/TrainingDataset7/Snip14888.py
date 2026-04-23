def get_previous_year(self, date):
        """Get the previous valid year."""
        return _get_next_prev(self, date, is_previous=True, period="year")