def _make_single_date_lookup(self, date):
        """
        Get the lookup kwargs for filtering on a single date.

        If the date field is a DateTimeField, we can't just filter on
        date_field=date because that doesn't take the time into account.
        """
        date_field = self.get_date_field()
        if self.uses_datetime_field:
            since = self._make_date_lookup_arg(date)
            until = self._make_date_lookup_arg(date + datetime.timedelta(days=1))
            return {
                "%s__gte" % date_field: since,
                "%s__lt" % date_field: until,
            }
        else:
            # Skip self._make_date_lookup_arg, it's a no-op in this branch.
            return {date_field: date}