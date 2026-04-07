def get_date_field(self):
        """Get the name of the date field to be used to filter by."""
        if self.date_field is None:
            raise ImproperlyConfigured(
                "%s.date_field is required." % self.__class__.__name__
            )
        return self.date_field