def __call__(self, value):
        cleaned = self.clean(value)
        limit_value = (
            self.limit_value() if callable(self.limit_value) else self.limit_value
        )
        params = {"limit_value": limit_value, "show_value": cleaned, "value": value}
        if self.compare(cleaned, limit_value):
            raise ValidationError(self.message, code=self.code, params=params)