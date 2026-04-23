def clean(self, value):
        """
        Validate the given value and return its "cleaned" value as an
        appropriate Python object. Raise ValidationError for any errors.
        """
        value = self.to_python(value)
        self.validate(value)
        self.run_validators(value)
        return value