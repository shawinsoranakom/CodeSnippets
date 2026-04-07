def test_migrate_nonexistent_app_label(self):
        with self.assertRaisesMessage(CommandError, self.nonexistent_app_error):
            call_command("migrate", "nonexistent_app")