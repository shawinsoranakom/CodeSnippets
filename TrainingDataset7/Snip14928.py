def get_dated_items(self):
        """Return (date_list, items, extra_context) for this request."""
        return self._get_dated_items(datetime.date.today())