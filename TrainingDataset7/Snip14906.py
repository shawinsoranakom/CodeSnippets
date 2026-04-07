def get_previous_week(self, date):
        """Get the previous valid week."""
        return _get_next_prev(self, date, is_previous=True, period="week")