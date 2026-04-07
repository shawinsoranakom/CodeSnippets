def test_migrate_and_makemigrations_autodetector_different(self):
        expected_error = Error(
            "The migrate and makemigrations commands must have the same "
            "autodetector.",
            hint=(
                "makemigrations.Command.autodetector is int, but "
                "migrate.Command.autodetector is MigrationAutodetector."
            ),
            id="commands.E001",
        )

        self.assertEqual(
            checks.run_checks(app_configs=self.apps.get_app_configs()),
            [expected_error],
        )