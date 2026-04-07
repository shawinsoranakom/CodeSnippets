def formfield(self, **kwargs):
        return super().formfield(
            **{
                "max_digits": self.max_digits,
                "decimal_places": self.decimal_places,
                "form_class": forms.DecimalField,
                **kwargs,
            }
        )