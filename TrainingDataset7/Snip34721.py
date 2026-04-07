def clean(self):
        cleaned_data = self.cleaned_data
        if cleaned_data.get("text") == "Raise non-field error":
            raise ValidationError("Non-field error.")
        return cleaned_data