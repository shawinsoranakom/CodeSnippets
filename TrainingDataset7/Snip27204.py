def test_apply_all_replaced_marks_replacement_as_applied(self):
        """
        Applying all replaced migrations marks replacement as applied (#24628).
        """
        recorder = MigrationRecorder(connection)
        # Place the database in a state where the replaced migrations are
        # partially applied: 0001 is applied, 0002 is not.
        recorder.record_applied("migrations", "0001_initial")
        executor = MigrationExecutor(connection)
        # Use fake because we don't actually have the first migration
        # applied, so the second will fail. And there's no need to actually
        # create/modify tables here, we're just testing the
        # MigrationRecord, which works the same with or without fake.
        executor.migrate([("migrations", "0002_second")], fake=True)

        # Because we've now applied 0001 and 0002 both, their squashed
        # replacement should be marked as applied.
        self.assertIn(
            ("migrations", "0001_squashed_0002"),
            recorder.applied_migrations(),
        )