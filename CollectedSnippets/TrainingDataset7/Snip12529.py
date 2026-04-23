def clean(self, value):
        value = super().clean(value)
        return self._coerce(value)