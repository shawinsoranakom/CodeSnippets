def test_sqlmigrate_nonexistent_app_label(self):
        with self.assertRaisesMessage(CommandError, self.nonexistent_app_error):
            call_command("sqlmigrate", "nonexistent_app", "0002")