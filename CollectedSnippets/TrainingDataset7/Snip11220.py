def to_python(self, value):
        if value is not None and not isinstance(value, uuid.UUID):
            input_form = "int" if isinstance(value, int) else "hex"
            try:
                return uuid.UUID(**{input_form: value})
            except (AttributeError, ValueError):
                raise exceptions.ValidationError(
                    self.error_messages["invalid"],
                    code="invalid",
                    params={"value": value},
                )
        return value