def test_prune_respect_app_label(self):
        recorder = MigrationRecorder(connection)
        recorder.record_applied("migrations", "0001_initial")
        recorder.record_applied("migrations", "0002_second")
        recorder.record_applied("migrations", "0001_squashed_0002")
        # Second app has squashed migrations with replaces.
        recorder.record_applied("migrations2", "0001_initial")
        recorder.record_applied("migrations2", "0002_second")
        recorder.record_applied("migrations2", "0001_squashed_0002")
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
                if migration[0] in ["migrations", "migrations2"]
            ]
            self.assertEqual(
                applied_migrations,
                [
                    ("migrations", "0001_squashed_0002"),
                    ("migrations2", "0001_initial"),
                    ("migrations2", "0002_second"),
                    ("migrations2", "0001_squashed_0002"),
                ],
            )
        finally:
            recorder.record_unapplied("migrations", "0001_initial")
            recorder.record_unapplied("migrations", "0001_second")
            recorder.record_unapplied("migrations", "0001_squashed_0002")
            recorder.record_unapplied("migrations2", "0001_initial")
            recorder.record_unapplied("migrations2", "0002_second")
            recorder.record_unapplied("migrations2", "0001_squashed_0002")