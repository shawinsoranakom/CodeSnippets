def __call__(self, value):
        if not isinstance(value, str) or len(value) > self.max_length:
            raise ValidationError(self.message, code=self.code, params={"value": value})
        if not self.accept_idna and not value.isascii():
            raise ValidationError(self.message, code=self.code, params={"value": value})
        super().__call__(value)