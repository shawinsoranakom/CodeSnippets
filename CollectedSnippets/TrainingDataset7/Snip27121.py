def test_makemigrations_with_invalid_custom_name(self):
        msg = "The migration name must be a valid Python identifier."
        with self.assertRaisesMessage(CommandError, msg):
            call_command(
                "makemigrations", "migrations", "--name", "invalid name", "--empty"
            )