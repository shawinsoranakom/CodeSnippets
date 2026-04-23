def get_next_year(self, date):
        """Get the next valid year."""
        return _get_next_prev(self, date, is_previous=False, period="year")