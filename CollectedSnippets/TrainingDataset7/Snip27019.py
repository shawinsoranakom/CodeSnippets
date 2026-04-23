def test_migrate_with_system_checks(self, mocked_check):
        out = io.StringIO()
        call_command("migrate", skip_checks=False, no_color=True, stdout=out)
        self.assertIn("Apply all migrations: migrated_app", out.getvalue())
        mocked_check.assert_called_once_with(databases=["default"])