def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": SimpleArrayField,
                "base_field": self.base_field.formfield(),
                "max_length": self.size,
                **kwargs,
            }
        )