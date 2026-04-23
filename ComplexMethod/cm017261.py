def _get_altered_foo_together_operations(self, option_name):
        for app_label, model_name in sorted(self.kept_model_keys):
            old_model_name = self.renamed_models.get(
                (app_label, model_name), model_name
            )
            old_model_state = self.from_state.models[app_label, old_model_name]
            new_model_state = self.to_state.models[app_label, model_name]

            # We run the old version through the field renames to account for
            # those
            old_value = old_model_state.options.get(option_name)
            old_value = (
                {
                    tuple(
                        self.renamed_fields.get((app_label, model_name, n), n)
                        for n in unique
                    )
                    for unique in old_value
                }
                if old_value
                else set()
            )

            new_value = new_model_state.options.get(option_name)
            new_value = set(new_value) if new_value else set()

            if old_value != new_value:
                dependencies = []
                for foo_togethers in new_value:
                    for field_name in foo_togethers:
                        field = new_model_state.get_field(field_name)
                        if field.remote_field and field.remote_field.model:
                            dependencies.extend(
                                self._get_dependencies_for_foreign_key(
                                    app_label,
                                    model_name,
                                    field,
                                    self.to_state,
                                )
                            )
                yield (
                    old_value,
                    new_value,
                    app_label,
                    model_name,
                    dependencies,
                )