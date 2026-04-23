def test_app_without_migrations(self):
        msg = "App 'unmigrated_app_simple' does not have migrations."
        with self.assertRaisesMessage(CommandError, msg):
            call_command("optimizemigration", "unmigrated_app_simple", "0001")