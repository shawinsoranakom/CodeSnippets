def to_python(self, value):
        value = super().to_python(value)
        if value in self.empty_values:
            return None
        if not isinstance(value, uuid.UUID):
            try:
                value = uuid.UUID(value)
            except ValueError:
                raise ValidationError(self.error_messages["invalid"], code="invalid")
        return value