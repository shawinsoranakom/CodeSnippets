def _make_date_lookup_arg(self, value):
        """
        Convert a date into a datetime when the date field is a DateTimeField.

        When time zone support is enabled, `date` is assumed to be in the
        current time zone, so that displayed items are consistent with the URL.
        """
        if self.uses_datetime_field:
            value = datetime.datetime.combine(value, datetime.time.min)
            if settings.USE_TZ:
                value = timezone.make_aware(value)
        return value