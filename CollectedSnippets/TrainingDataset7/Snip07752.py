def to_python(self, value):
        if not value:
            return {}
        if not isinstance(value, dict):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise ValidationError(
                    self.error_messages["invalid_json"],
                    code="invalid_json",
                )

        if not isinstance(value, dict):
            raise ValidationError(
                self.error_messages["invalid_format"],
                code="invalid_format",
            )

        # Cast everything to strings for ease.
        for key, val in value.items():
            if val is not None:
                val = str(val)
            value[key] = val
        return value