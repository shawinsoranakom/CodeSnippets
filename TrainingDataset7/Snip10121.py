def generate_altered_options(self):
        """
        Work out if any non-schema-affecting options have changed and make an
        operation to represent them in state changes (in case Python code in
        migrations needs them).
        """
        models_to_check = self.kept_model_keys.union(
            self.kept_proxy_keys,
            self.kept_unmanaged_keys,
            # unmanaged converted to managed
            self.old_unmanaged_keys & self.new_model_keys,
            # managed converted to unmanaged
            self.old_model_keys & self.new_unmanaged_keys,
        )

        for app_label, model_name in sorted(models_to_check):
            old_model_name = self.renamed_models.get(
                (app_label, model_name), model_name
            )
            old_model_state = self.from_state.models[app_label, old_model_name]
            new_model_state = self.to_state.models[app_label, model_name]
            old_options = {
                key: value
                for key, value in old_model_state.options.items()
                if key in AlterModelOptions.ALTER_OPTION_KEYS
            }
            new_options = {
                key: value
                for key, value in new_model_state.options.items()
                if key in AlterModelOptions.ALTER_OPTION_KEYS
            }
            if old_options != new_options:
                self.add_operation(
                    app_label,
                    operations.AlterModelOptions(
                        name=model_name,
                        options=new_options,
                    ),
                )