def test_migrate_prune(self):
        """
        With prune=True, references to migration files deleted from the
        migrations module (such as after being squashed) are removed from the
        django_migrations table.
        """
        recorder = MigrationRecorder(connection)
        recorder.record_applied("migrations", "0001_initial")
        recorder.record_applied("migrations", "0002_second")
        recorder.record_applied("migrations", "0001_squashed_0002")
        out = io.StringIO()
        try:
            call_command("migrate", "migrations", prune=True, stdout=out, no_color=True)
            self.assertEqual(
                out.getvalue(),
                "Pruning migrations:\n"
                "  Pruning migrations.0001_initial OK\n"
                "  Pruning migrations.0002_second OK\n",
            )
            applied_migrations = [
                migration
                for migration in recorder.applied_migrations()
                if migration[0] == "migrations"
            ]
            self.assertEqual(applied_migrations, [("migrations", "0001_squashed_0002")])
        finally:
            recorder.record_unapplied("migrations", "0001_initial")
            recorder.record_unapplied("migrations", "0001_second")
            recorder.record_unapplied("migrations", "0001_squashed_0002")