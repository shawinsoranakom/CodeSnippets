def add_update_values(self, values):
        """
        Convert a dictionary of field name to value mappings into an update
        query. This is the entry point for the public update() method on
        querysets.
        """
        values_seq = []
        for name, val in values.items():
            field = self.get_meta().get_field(name)
            model = field.model._meta.concrete_model
            if field.name == "pk" and model._meta.is_composite_pk:
                raise FieldError(
                    "Composite primary key fields must be updated individually."
                )
            if not field.concrete:
                raise FieldError(
                    "Cannot update model field %r (only concrete fields are permitted)."
                    % field
                )
            if model is not self.get_meta().concrete_model:
                self.add_related_update(model, field, val)
                continue
            values_seq.append((field, model, val))
        return self.add_update_fields(values_seq)