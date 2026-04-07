def get_ordering(self):
        """
        Return the field or fields to use for ordering the queryset; use the
        date field by default.
        """
        return "-%s" % self.get_date_field() if self.ordering is None else self.ordering