def clean(self, value):
        value = super().clean(value)
        return [self.base_field.clean(val) for val in value]