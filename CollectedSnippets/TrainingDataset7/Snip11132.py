def formfield(self, **kwargs):
        # As with CharField, this will cause email validation to be performed
        # twice.
        return super().formfield(
            **{
                "form_class": forms.EmailField,
                **kwargs,
            }
        )