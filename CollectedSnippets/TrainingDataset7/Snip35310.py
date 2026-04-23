def clean_field(self):
        value = self.cleaned_data.get("field", "")
        if value == "invalid":
            raise ValidationError("invalid value")
        return value