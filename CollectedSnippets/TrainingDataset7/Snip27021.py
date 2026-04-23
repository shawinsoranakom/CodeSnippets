def test_migrate_runs_database_system_checks(self):
        original_checks = registry.registered_checks.copy()
        self.addCleanup(setattr, registry, "registered_checks", original_checks)

        out = io.StringIO()
        mock_check = mock.Mock(return_value=[])
        register(mock_check, Tags.database)

        call_command("migrate", skip_checks=False, no_color=True, stdout=out)
        self.assertIn("Apply all migrations: migrated_app", out.getvalue())
        mock_check.assert_called_once_with(app_configs=None, databases=["default"])