def get_previous_day(self, date):
        """Get the previous valid day."""
        return _get_next_prev(self, date, is_previous=True, period="day")