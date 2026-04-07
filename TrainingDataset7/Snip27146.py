def test_double_replaced_migrations_are_recorded(self):
        """
        All recursively replaced migrations should be recorded/unrecorded, when
        migrating an app with double squashed migrations.
        """
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_squashed_double"
        ):
            recorder = MigrationRecorder(connection)
            applied_app_labels = [
                app_label for app_label, _ in recorder.applied_migrations()
            ]
            self.assertNotIn("migrations", applied_app_labels)

            call_command(
                "migrate", "migrations", "--plan", interactive=False, stdout=out
            )
            migration_plan = re.findall("migrations.(.+)\n", out.getvalue())
            # Only the top-level replacement migration should be applied.
            self.assertEqual(migration_plan, ["0005_squashed_0003_and_0004"])

            call_command("migrate", "migrations", interactive=False, verbosity=0)
            applied_migrations = recorder.applied_migrations()
            # Make sure all replaced migrations are recorded.
            self.assertIn(("migrations", "0001_initial"), applied_migrations)
            self.assertIn(("migrations", "0002_auto"), applied_migrations)
            self.assertIn(
                ("migrations", "0003_squashed_0001_and_0002"), applied_migrations
            )
            self.assertIn(("migrations", "0004_auto"), applied_migrations)
            self.assertIn(
                ("migrations", "0005_squashed_0003_and_0004"), applied_migrations
            )

            # Unapply all migrations from this app.
            call_command(
                "migrate", "migrations", "zero", interactive=False, verbosity=0
            )
            applied_app_labels = [
                app_label for app_label, _ in recorder.applied_migrations()
            ]
            self.assertNotIn("migrations", applied_app_labels)