def test_migrate_record_squashed(self):
        """
        Running migrate for a squashed migration should record as run
        if all of the replaced migrations have been run (#25231).
        """
        recorder = MigrationRecorder(connection)
        recorder.record_applied("migrations", "0001_initial")
        recorder.record_applied("migrations", "0002_second")
        out = io.StringIO()
        call_command("showmigrations", "migrations", stdout=out, no_color=True)
        self.assertEqual(
            "migrations\n"
            " [-] 0001_squashed_0002 (2 squashed migrations) "
            "run 'manage.py migrate' to finish recording.\n",
            out.getvalue().lower(),
        )

        out = io.StringIO()
        call_command("migrate", "migrations", verbosity=0)
        call_command("showmigrations", "migrations", stdout=out, no_color=True)
        self.assertEqual(
            "migrations\n [x] 0001_squashed_0002 (2 squashed migrations)\n",
            out.getvalue().lower(),
        )
        self.assertIn(
            ("migrations", "0001_squashed_0002"), recorder.applied_migrations()
        )