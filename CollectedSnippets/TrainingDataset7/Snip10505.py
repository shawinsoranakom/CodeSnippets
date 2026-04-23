def remove_field(self, app_label, model_name, name):
        model_key = app_label, model_name
        model_state = self.models[model_key]
        old_field = model_state.fields.pop(name)
        if self._relations is not None:
            self.resolve_model_field_relations(model_key, name, old_field)
        # Delay rendering of relationships if it's not a relational field.
        delay = not old_field.is_relation
        self.reload_model(*model_key, delay=delay)