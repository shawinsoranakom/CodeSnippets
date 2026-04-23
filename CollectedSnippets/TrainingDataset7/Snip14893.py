def get_next_month(self, date):
        """Get the next valid month."""
        return _get_next_prev(self, date, is_previous=False, period="month")