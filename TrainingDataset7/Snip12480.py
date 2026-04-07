def validate(self, value):
        super().validate(value)
        if value in self.empty_values:
            return
        if not value.is_finite():
            raise ValidationError(
                self.error_messages["invalid"],
                code="invalid",
                params={"value": value},
            )