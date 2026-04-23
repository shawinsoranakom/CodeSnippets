def get_next_week(self, date):
        """Get the next valid week."""
        return _get_next_prev(self, date, is_previous=False, period="week")