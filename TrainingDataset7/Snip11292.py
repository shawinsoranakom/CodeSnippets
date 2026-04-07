def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": forms.FileField,
                "max_length": self.max_length,
                **kwargs,
            }
        )