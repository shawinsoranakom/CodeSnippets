def clean(self):
        parent = self.cleaned_data.get("parent")
        if parent.family_name and parent.family_name != self.cleaned_data.get(
            "family_name"
        ):
            raise ValidationError(
                "Children must share a family name with their parents "
                + "in this contrived test case"
            )
        return super().clean()