def adapt_datetimefield_value(self, value):
        """
        Transform a datetime value to an object compatible with what is
        expected by the backend driver for datetime columns.

        If naive datetime is passed assumes that is in UTC. Normally Django
        models.DateTimeField makes sure that if USE_TZ is True passed datetime
        is timezone aware.
        """

        if value is None:
            return None

        # oracledb doesn't support tz-aware datetimes
        if timezone.is_aware(value):
            if settings.USE_TZ:
                value = timezone.make_naive(value, self.connection.timezone)
            else:
                raise ValueError(
                    "Oracle backend does not support timezone-aware datetimes when "
                    "USE_TZ is False."
                )

        return Oracle_datetime.from_datetime(value)