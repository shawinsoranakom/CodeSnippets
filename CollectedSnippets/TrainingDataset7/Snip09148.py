def __call__(self, value):
        if "\x00" in str(value):
            raise ValidationError(self.message, code=self.code, params={"value": value})