def clean(self):
        cleaned_data = self.cleaned_data
        title1 = cleaned_data.get("title1")
        title2 = cleaned_data.get("title2")
        if title1 != title2:
            raise ValidationError("The two titles must be the same")
        return cleaned_data