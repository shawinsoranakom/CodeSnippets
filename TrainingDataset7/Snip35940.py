def test_calling_a_command_with_no_app_labels_and_parameters_raise_command_error(
        self,
    ):
        with self.assertRaises(CommandError):
            management.call_command("hal")