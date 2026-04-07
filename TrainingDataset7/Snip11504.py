def get_object(self, instance):
        if self.field.remote_field.parent_link:
            deferred = instance.get_deferred_fields()
            # Because it's a parent link, all the data is available in the
            # instance, so populate the parent model with this data.
            rel_model = self.field.remote_field.model
            fields = [field.attname for field in rel_model._meta.concrete_fields]

            # If any of the related model's fields are deferred, fallback to
            # fetching all fields from the related model. This avoids a query
            # on the related model for every deferred field.
            if not any(field in fields for field in deferred):
                kwargs = {field: getattr(instance, field) for field in fields}
                obj = rel_model(**kwargs)
                obj._state.adding = instance._state.adding
                obj._state.db = instance._state.db
                obj._state.fetch_mode = instance._state.fetch_mode
                return obj
        return super().get_object(instance)