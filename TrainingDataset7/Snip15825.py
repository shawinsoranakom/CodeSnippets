def test_base_command_with_options(self):
        """
        User BaseCommands can execute with multiple options when a label is
        provided
        """
        args = ["base_command", "testlabel", "-a", "x", "--option_b=y"]
        expected_labels = "('testlabel',)"
        self._test_base_command(args, expected_labels, option_a="'x'", option_b="'y'")