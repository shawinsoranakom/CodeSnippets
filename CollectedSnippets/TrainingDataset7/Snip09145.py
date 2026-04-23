def __call__(self, value):
        extension = Path(value.name).suffix[1:].lower()
        if (
            self.allowed_extensions is not None
            and extension not in self.allowed_extensions
        ):
            raise ValidationError(
                self.message,
                code=self.code,
                params={
                    "extension": extension,
                    "allowed_extensions": ", ".join(self.allowed_extensions),
                    "value": value,
                },
            )