def to_python(self, value):
        if value in self.empty_values:
            return None
        self.validate_no_null_characters(value)
        try:
            key = self.to_field_name or "pk"
            if isinstance(value, self.queryset.model):
                value = getattr(value, key)
            value = self.queryset.get(**{key: value})
        except (
            ValueError,
            TypeError,
            self.queryset.model.DoesNotExist,
            ValidationError,
        ):
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            )
        return value