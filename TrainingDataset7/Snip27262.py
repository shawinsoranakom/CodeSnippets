def test_check_consistent_history(self):
        loader = MigrationLoader(connection=None)
        loader.check_consistent_history(connection)
        recorder = MigrationRecorder(connection)
        self.record_applied(recorder, "migrations", "0002_second")
        msg = (
            "Migration migrations.0002_second is applied before its dependency "
            "migrations.0001_initial on database 'default'."
        )
        with self.assertRaisesMessage(InconsistentMigrationHistory, msg):
            loader.check_consistent_history(connection)