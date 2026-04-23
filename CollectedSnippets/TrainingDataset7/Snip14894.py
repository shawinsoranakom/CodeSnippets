def get_previous_month(self, date):
        """Get the previous valid month."""
        return _get_next_prev(self, date, is_previous=True, period="month")