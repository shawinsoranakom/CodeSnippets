def test_base_command(self):
        "User BaseCommands can execute when a label is provided"
        args = ["base_command", "testlabel"]
        expected_labels = "('testlabel',)"
        self._test_base_command(args, expected_labels)