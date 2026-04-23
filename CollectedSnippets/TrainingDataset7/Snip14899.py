def get_next_day(self, date):
        """Get the next valid day."""
        return _get_next_prev(self, date, is_previous=False, period="day")