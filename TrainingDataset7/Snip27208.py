def test_migrations_not_applied_on_deferred_sql_failure(self):
        """Migrations are not recorded if deferred SQL application fails."""

        class DeferredSQL:
            def __str__(self):
                raise DatabaseError("Failed to apply deferred SQL")

        class Migration(migrations.Migration):
            atomic = False

            def apply(self, project_state, schema_editor, collect_sql=False):
                schema_editor.deferred_sql.append(DeferredSQL())

        executor = MigrationExecutor(connection)
        with self.assertRaisesMessage(DatabaseError, "Failed to apply deferred SQL"):
            executor.apply_migration(
                ProjectState(),
                Migration("0001_initial", "deferred_sql"),
            )
        # The migration isn't recorded as applied since it failed.
        migration_recorder = MigrationRecorder(connection)
        self.assertIs(
            migration_recorder.migration_qs.filter(
                app="deferred_sql",
                name="0001_initial",
            ).exists(),
            False,
        )