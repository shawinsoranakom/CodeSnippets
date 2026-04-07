def rename_model(self, app_label, old_name, new_name):
        # Add a new model.
        old_name_lower = old_name.lower()
        new_name_lower = new_name.lower()
        renamed_model = self.models[app_label, old_name_lower].clone()
        renamed_model.name = new_name
        self.models[app_label, new_name_lower] = renamed_model
        # Repoint all fields pointing to the old model to the new one.
        old_model_tuple = (app_label, old_name_lower)
        new_remote_model = f"{app_label}.{new_name}"
        to_reload = set()
        for model_state, name, field, reference in get_references(
            self, old_model_tuple
        ):
            changed_field = None
            if reference.to:
                changed_field = field.clone()
                changed_field.remote_field.model = new_remote_model
            if reference.through:
                if changed_field is None:
                    changed_field = field.clone()
                changed_field.remote_field.through = new_remote_model
            if changed_field:
                model_state.fields[name] = changed_field
                to_reload.add((model_state.app_label, model_state.name_lower))
        if self._relations is not None:
            old_name_key = app_label, old_name_lower
            new_name_key = app_label, new_name_lower
            if old_name_key in self._relations:
                self._relations[new_name_key] = self._relations.pop(old_name_key)
            for model_relations in self._relations.values():
                if old_name_key in model_relations:
                    model_relations[new_name_key] = model_relations.pop(old_name_key)
        # Reload models related to old model before removing the old model.
        self.reload_models(to_reload, delay=True)
        # Remove the old model.
        self.remove_model(app_label, old_name_lower)
        self.reload_model(app_label, new_name_lower, delay=True)