def unapply_migration(self, state, migration, fake=False):
        """Run a migration backwards."""
        if self.progress_callback:
            self.progress_callback("unapply_start", migration, fake)
        if not fake:
            with self.connection.schema_editor(
                atomic=migration.atomic
            ) as schema_editor:
                state = migration.unapply(state, schema_editor)
        self.record_migration(migration.app_label, migration.name, forward=False)
        # Report progress
        if self.progress_callback:
            self.progress_callback("unapply_success", migration, fake)
        return state