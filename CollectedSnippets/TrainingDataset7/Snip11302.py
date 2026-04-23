def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": forms.ImageField,
                **kwargs,
            }
        )