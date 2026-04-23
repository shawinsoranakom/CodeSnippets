def _get_dated_items(self, date):
        """
        Do the actual heavy lifting of getting the dated items; this accepts a
        date object so that TodayArchiveView can be trivial.
        """
        lookup_kwargs = self._make_single_date_lookup(date)
        qs = self.get_dated_queryset(**lookup_kwargs)

        return (
            None,
            qs,
            {
                "day": date,
                "previous_day": self.get_previous_day(date),
                "next_day": self.get_next_day(date),
                "previous_month": self.get_previous_month(date),
                "next_month": self.get_next_month(date),
            },
        )