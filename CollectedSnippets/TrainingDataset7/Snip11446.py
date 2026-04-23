def formfield(self, *, using=None, **kwargs):
        if isinstance(self.remote_field.model, str):
            raise ValueError(
                "Cannot create form field for %r yet, because "
                "its related model %r has not been loaded yet"
                % (self.name, self.remote_field.model)
            )
        return super().formfield(
            **{
                "form_class": forms.ModelChoiceField,
                "queryset": self.remote_field.model._default_manager.using(using),
                "to_field_name": self.remote_field.field_name,
                **kwargs,
                "blank": self.blank,
            }
        )