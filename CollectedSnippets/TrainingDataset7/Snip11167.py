def formfield(self, **kwargs):
        return super().formfield(
            **{
                "protocol": self.protocol,
                "form_class": forms.GenericIPAddressField,
                **kwargs,
            }
        )