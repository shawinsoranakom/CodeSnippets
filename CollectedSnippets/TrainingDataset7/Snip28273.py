def __setattr__(self, key, value):
        if self._should_error is True:
            raise ValidationError(message="Cannot set attribute", code="invalid")
        super().__setattr__(key, value)