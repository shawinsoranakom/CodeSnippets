def failing_helper(self, field_name):
        if field_name in self.failing_fields:
            errors = [
                ValidationError(error, code="invalid")
                for error in self.failing_fields[field_name]
            ]
            raise ValidationError(errors)
        return self.cleaned_data[field_name]