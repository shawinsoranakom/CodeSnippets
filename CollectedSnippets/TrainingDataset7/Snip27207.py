def test_migrations_applied_and_recorded_atomically(self):
        """Migrations are applied and recorded atomically."""

        class Migration(migrations.Migration):
            operations = [
                migrations.CreateModel(
                    "model",
                    [
                        ("id", models.AutoField(primary_key=True)),
                    ],
                ),
            ]

        executor = MigrationExecutor(connection)
        with mock.patch(
            "django.db.migrations.executor.MigrationExecutor.record_migration"
        ) as record_migration:
            record_migration.side_effect = RuntimeError("Recording migration failed.")
            with self.assertRaisesMessage(RuntimeError, "Recording migration failed."):
                executor.apply_migration(
                    ProjectState(),
                    Migration("0001_initial", "record_migration"),
                )
                executor.migrate([("migrations", "0001_initial")])
        # The migration isn't recorded as applied since it failed.
        migration_recorder = MigrationRecorder(connection)
        self.assertIs(
            migration_recorder.migration_qs.filter(
                app="record_migration",
                name="0001_initial",
            ).exists(),
            False,
        )
        self.assertTableNotExists("record_migration_model")