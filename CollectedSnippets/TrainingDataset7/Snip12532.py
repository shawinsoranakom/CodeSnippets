def clean(self, value):
        """
        Validate the given value against all of self.fields, which is a
        list of Field instances.
        """
        super().clean(value)
        for field in self.fields:
            value = field.clean(value)
        return value