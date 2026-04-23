def resolve_related_fields(self):
        related_fields = super().resolve_related_fields()
        for from_field, to_field in related_fields:
            if (
                to_field
                and to_field.model != self.remote_field.model._meta.concrete_model
            ):
                raise exceptions.FieldError(
                    "'%s.%s' refers to field '%s' which is not local to model "
                    "'%s'."
                    % (
                        self.model._meta.label,
                        self.name,
                        to_field.name,
                        self.remote_field.model._meta.concrete_model._meta.label,
                    )
                )
        return related_fields