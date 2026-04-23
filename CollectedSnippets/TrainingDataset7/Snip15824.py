def test_base_command_with_option(self):
        "User BaseCommands can execute with options when a label is provided"
        args = ["base_command", "testlabel", "--option_a=x"]
        expected_labels = "('testlabel',)"
        self._test_base_command(args, expected_labels, option_a="'x'")