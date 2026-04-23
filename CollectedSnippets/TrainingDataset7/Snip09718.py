def convert_datetimefield_value(self, value, expression, connection):
        if value is not None:
            value = timezone.make_aware(value, self.connection.timezone)
        return value