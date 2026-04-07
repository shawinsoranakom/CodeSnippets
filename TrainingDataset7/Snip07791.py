def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != "postgresql" or not router.allow_migrate(
            schema_editor.connection.alias, app_label, **self.hints
        ):
            return
        if not self.extension_exists(schema_editor, self.name):
            schema_editor.execute(
                "CREATE EXTENSION IF NOT EXISTS %s"
                % schema_editor.quote_name(self.name)
            )
        # Clear cached, stale oids.
        get_hstore_oids.cache_clear()
        get_citext_oids.cache_clear()
        # Registering new type handlers cannot be done before the extension is
        # installed, otherwise a subsequent data migration would use the same
        # connection.
        register_type_handlers(schema_editor.connection)
        if hasattr(schema_editor.connection, "register_geometry_adapters"):
            schema_editor.connection.register_geometry_adapters(
                schema_editor.connection.connection, True
            )