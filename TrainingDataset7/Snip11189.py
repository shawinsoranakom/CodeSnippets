def formfield(self, **kwargs):
        # Passing max_length to forms.CharField means that the value's length
        # will be validated twice. This is considered acceptable since we want
        # the value in the form field (to pass into widget for example).
        return super().formfield(
            **{
                "max_length": self.max_length,
                **({} if self.choices is not None else {"widget": forms.Textarea}),
                **kwargs,
            }
        )