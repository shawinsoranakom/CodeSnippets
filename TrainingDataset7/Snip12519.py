def validate(self, value):
        """Validate that the input is in self.choices."""
        super().validate(value)
        if value and not self.valid_value(value):
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            )