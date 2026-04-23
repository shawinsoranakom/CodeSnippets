def test_check_consistent_history_squashed(self):
        """
        MigrationLoader.check_consistent_history() should ignore unapplied
        squashed migrations that have all of their `replaces` applied.
        """
        loader = MigrationLoader(connection=None)
        recorder = MigrationRecorder(connection)
        self.record_applied(recorder, "migrations", "0001_initial")
        self.record_applied(recorder, "migrations", "0002_second")
        loader.check_consistent_history(connection)
        self.record_applied(recorder, "migrations", "0003_third")
        loader.check_consistent_history(connection)