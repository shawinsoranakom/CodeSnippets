def get_dated_items(self):
        """Return (date_list, items, extra_context) for this request."""
        year = self.get_year()

        date_field = self.get_date_field()
        date = _date_from_string(year, self.get_year_format())

        since = self._make_date_lookup_arg(date)
        until = self._make_date_lookup_arg(self._get_next_year(date))
        lookup_kwargs = {
            "%s__gte" % date_field: since,
            "%s__lt" % date_field: until,
        }

        qs = self.get_dated_queryset(**lookup_kwargs)
        date_list = self.get_date_list(qs)

        if not self.get_make_object_list():
            # We need this to be a queryset since parent classes introspect it
            # to find information about the model.
            qs = qs.none()

        return (
            date_list,
            qs,
            {
                "year": date,
                "next_year": self.get_next_year(date),
                "previous_year": self.get_previous_year(date),
            },
        )