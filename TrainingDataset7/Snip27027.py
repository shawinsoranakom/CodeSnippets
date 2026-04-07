def test_migrate_fake_initial_case_insensitive(self):
        with override_settings(
            MIGRATION_MODULES={
                "migrations": "migrations.test_fake_initial_case_insensitive.initial",
            }
        ):
            call_command("migrate", "migrations", "0001", verbosity=0)
            call_command("migrate", "migrations", "zero", fake=True, verbosity=0)

        with override_settings(
            MIGRATION_MODULES={
                "migrations": (
                    "migrations.test_fake_initial_case_insensitive.fake_initial"
                ),
            }
        ):
            out = io.StringIO()
            call_command(
                "migrate",
                "migrations",
                "0001",
                fake_initial=True,
                stdout=out,
                verbosity=1,
                no_color=True,
            )
            self.assertIn(
                "migrations.0001_initial... faked",
                out.getvalue().lower(),
            )