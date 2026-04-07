def test_base_command_multiple_label(self):
        "User BaseCommands can execute when no labels are provided"
        args = ["base_command", "testlabel", "anotherlabel"]
        expected_labels = "('testlabel', 'anotherlabel')"
        self._test_base_command(args, expected_labels)