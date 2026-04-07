def test_makemigrations_update_dependency_migration(self):
        with self.temporary_migration_module(app_label="book_app"):
            msg = (
                "Cannot update migration 'book_app.0001_initial' that migrations "
                "'author_app.0002_alter_id' depend on."
            )
            with self.assertRaisesMessage(CommandError, msg):
                call_command("makemigrations", "book_app", update=True)