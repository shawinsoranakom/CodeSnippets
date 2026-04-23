def _get_dependencies_for_model(self, app_label, model_name):
        """Return foreign key dependencies of the given model."""
        dependencies = []
        model_state = self.to_state.models[app_label, model_name]
        for field in model_state.fields.values():
            if field.is_relation:
                dependencies.extend(
                    self._get_dependencies_for_foreign_key(
                        app_label,
                        model_name,
                        field,
                        self.to_state,
                    )
                )
        return dependencies