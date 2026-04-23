def test_custom_label_command_custom_missing_args_message(self):
        class Command(LabelCommand):
            missing_args_message = "Missing argument."

        with self.assertRaisesMessage(CommandError, "Error: Missing argument."):
            call_command(Command())