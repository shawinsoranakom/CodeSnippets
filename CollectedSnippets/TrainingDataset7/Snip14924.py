def get_dated_items(self):
        """Return (date_list, items, extra_context) for this request."""
        year = self.get_year()
        month = self.get_month()

        date_field = self.get_date_field()
        date = _date_from_string(
            year, self.get_year_format(), month, self.get_month_format()
        )

        since = self._make_date_lookup_arg(date)
        until = self._make_date_lookup_arg(self._get_next_month(date))
        lookup_kwargs = {
            "%s__gte" % date_field: since,
            "%s__lt" % date_field: until,
        }

        qs = self.get_dated_queryset(**lookup_kwargs)
        date_list = self.get_date_list(qs)

        return (
            date_list,
            qs,
            {
                "month": date,
                "next_month": self.get_next_month(date),
                "previous_month": self.get_previous_month(date),
            },
        )