def clean(self):
        if self.cleaned_data.get("field") == "invalid_non_field":
            raise ValidationError("non-field error")
        return self.cleaned_data