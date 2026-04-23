def test_squashmigrations_nonexistent_app_label(self):
        with self.assertRaisesMessage(CommandError, self.nonexistent_app_error):
            call_command("squashmigrations", "nonexistent_app", "0002")