def database_forwards(self, app_label, schema_editor, from_state, to_state):
        to_model = to_state.apps.get_model(app_label, self.name)
        if self.allow_migrate_model(schema_editor.connection.alias, to_model):
            from_model = from_state.apps.get_model(app_label, self.name)
            # Remove a field if we need to
            if (
                from_model._meta.order_with_respect_to
                and not to_model._meta.order_with_respect_to
            ):
                schema_editor.remove_field(
                    from_model, from_model._meta.get_field("_order")
                )
            # Add a field if we need to (altering the column is untouched as
            # it's likely a rename)
            elif (
                to_model._meta.order_with_respect_to
                and not from_model._meta.order_with_respect_to
            ):
                field = to_model._meta.get_field("_order")
                if not field.has_default():
                    field.default = 0
                schema_editor.add_field(
                    from_model,
                    field,
                )