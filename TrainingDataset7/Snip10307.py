def database_forwards(self, app_label, schema_editor, from_state, to_state):
        new_model = to_state.apps.get_model(app_label, self.name)
        if self.allow_migrate_model(schema_editor.connection.alias, new_model):
            from_model_state = from_state.models[app_label, self.name_lower]
            to_model_state = to_state.models[app_label, self.name_lower]
            alter_together = getattr(schema_editor, "alter_%s" % self.option_name)
            alter_together(
                new_model,
                from_model_state.options.get(self.option_name) or set(),
                to_model_state.options.get(self.option_name) or set(),
            )