def test_custom_label_command_none_missing_args_message(self):
        class Command(LabelCommand):
            missing_args_message = None

        with self.assertRaisesMessage(CommandError, ""):
            call_command(Command())