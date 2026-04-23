def clean(self):
        cleaned_data = super().clean()
        if "confirm" not in cleaned_data:
            raise forms.ValidationError("You must confirm the delete.")