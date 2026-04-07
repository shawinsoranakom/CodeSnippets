def __call__(self, value):
        if self.offset is None:
            super().__call__(value)
        else:
            cleaned = self.clean(value)
            limit_value = (
                self.limit_value() if callable(self.limit_value) else self.limit_value
            )
            if self.compare(cleaned, limit_value):
                offset = cleaned.__class__(self.offset)
                params = {
                    "limit_value": limit_value,
                    "offset": offset,
                    "valid_value1": offset + limit_value,
                    "valid_value2": offset + 2 * limit_value,
                }
                raise ValidationError(self.message, code=self.code, params=params)