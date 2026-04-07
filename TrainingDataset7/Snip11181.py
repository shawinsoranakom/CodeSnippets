def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": forms.SlugField,
                "allow_unicode": self.allow_unicode,
                **kwargs,
            }
        )