def test_base_command_no_label(self):
        "User BaseCommands can execute when no labels are provided"
        args = ["base_command"]
        expected_labels = "()"
        self._test_base_command(args, expected_labels)