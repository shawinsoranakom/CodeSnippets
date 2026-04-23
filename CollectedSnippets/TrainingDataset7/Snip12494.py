def to_python(self, value):
        if value in self.empty_values:
            return None
        if isinstance(value, datetime.timedelta):
            return value
        try:
            value = parse_duration(str(value))
        except OverflowError:
            raise ValidationError(
                self.error_messages["overflow"].format(
                    min_days=datetime.timedelta.min.days,
                    max_days=datetime.timedelta.max.days,
                ),
                code="overflow",
            )
        if value is None:
            raise ValidationError(self.error_messages["invalid"], code="invalid")
        return value