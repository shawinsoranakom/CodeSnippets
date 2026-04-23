def test_optimizemigration_nonexistent_app_label(self):
        with self.assertRaisesMessage(CommandError, self.nonexistent_app_error):
            call_command("optimizemigration", "nonexistent_app", "0002")