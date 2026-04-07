def get_dated_items(self):
        """Return (date_list, items, extra_context) for this request."""
        year = self.get_year()
        week = self.get_week()

        date_field = self.get_date_field()
        week_format = self.get_week_format()
        week_choices = {"%W": "1", "%U": "0", "%V": "1"}
        try:
            week_start = week_choices[week_format]
        except KeyError:
            raise ValueError(
                "Unknown week format %r. Choices are: %s"
                % (
                    week_format,
                    ", ".join(sorted(week_choices)),
                )
            )
        year_format = self.get_year_format()
        if week_format == "%V" and year_format != "%G":
            raise ValueError(
                "ISO week directive '%s' is incompatible with the year "
                "directive '%s'. Use the ISO year '%%G' instead."
                % (
                    week_format,
                    year_format,
                )
            )
        date = _date_from_string(year, year_format, week_start, "%w", week, week_format)
        since = self._make_date_lookup_arg(date)
        until = self._make_date_lookup_arg(self._get_next_week(date))
        lookup_kwargs = {
            "%s__gte" % date_field: since,
            "%s__lt" % date_field: until,
        }

        qs = self.get_dated_queryset(**lookup_kwargs)

        return (
            None,
            qs,
            {
                "week": date,
                "next_week": self.get_next_week(date),
                "previous_week": self.get_previous_week(date),
            },
        )