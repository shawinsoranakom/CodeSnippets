def get_dated_items(self):
        """Return (date_list, items, extra_context) for this request."""
        qs = self.get_dated_queryset()
        date_list = self.get_date_list(qs, ordering="DESC")

        if not date_list:
            qs = qs.none()

        return (date_list, qs, {})