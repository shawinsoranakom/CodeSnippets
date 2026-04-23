def convert_trunc_expression(self, value, expression):
        if isinstance(expression.output_field, models.DateTimeField):
            if not settings.USE_TZ:
                pass
            elif value is not None:
                value = value.replace(tzinfo=None)
                value = timezone.make_aware(value, expression.tzinfo)
            elif not self.connection.features.has_zoneinfo_database:
                raise ValueError(
                    "Database returned an invalid datetime value. Are time "
                    "zone definitions for your database installed?"
                )
        elif isinstance(value, datetime.datetime):
            if isinstance(expression.output_field, models.DateField):
                value = value.date()
            elif isinstance(expression.output_field, models.TimeField):
                value = value.time()
        return value