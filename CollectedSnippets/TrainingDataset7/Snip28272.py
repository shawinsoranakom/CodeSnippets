def __setattr__(self, key, value):
        if self._should_error is True:
            raise ValidationError(message={key: "Cannot set attribute"}, code="invalid")
        super().__setattr__(key, value)