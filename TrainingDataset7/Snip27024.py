def test_unknown_prefix(self):
        msg = "Cannot find a migration matching 'nonexistent' from app 'migrations'."
        with self.assertRaisesMessage(CommandError, msg):
            call_command(
                "migrate", app_label="migrations", migration_name="nonexistent"
            )