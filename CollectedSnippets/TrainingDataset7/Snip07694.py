def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": forms.HStoreField,
                **kwargs,
            }
        )