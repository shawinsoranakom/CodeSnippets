def generate_altered_db_table(self):
        models_to_check = self.kept_model_keys.union(
            self.kept_proxy_keys, self.kept_unmanaged_keys
        )
        for app_label, model_name in sorted(models_to_check):
            old_model_name = self.renamed_models.get(
                (app_label, model_name), model_name
            )
            old_model_state = self.from_state.models[app_label, old_model_name]
            new_model_state = self.to_state.models[app_label, model_name]
            old_db_table_name = old_model_state.options.get("db_table")
            new_db_table_name = new_model_state.options.get("db_table")
            if old_db_table_name != new_db_table_name:
                self.add_operation(
                    app_label,
                    operations.AlterModelTable(
                        name=model_name,
                        table=new_db_table_name,
                    ),
                )