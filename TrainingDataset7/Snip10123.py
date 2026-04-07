def generate_altered_managers(self):
        for app_label, model_name in sorted(self.kept_model_keys):
            old_model_name = self.renamed_models.get(
                (app_label, model_name), model_name
            )
            old_model_state = self.from_state.models[app_label, old_model_name]
            new_model_state = self.to_state.models[app_label, model_name]
            if old_model_state.managers != new_model_state.managers:
                self.add_operation(
                    app_label,
                    operations.AlterModelManagers(
                        name=model_name,
                        managers=new_model_state.managers,
                    ),
                )