def test_readonly_database(self):
        """
        runserver.check_migrations() doesn't choke when a database is
        read-only.
        """
        with mock.patch.object(MigrationRecorder, "has_table", return_value=False):
            self.cmd.check_migrations()
        # You have # ...
        self.assertIn("unapplied migration(s)", self.output.getvalue())