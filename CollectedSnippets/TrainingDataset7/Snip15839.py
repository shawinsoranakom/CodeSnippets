def test_label_command_no_label(self):
        "User LabelCommands raise an error if no label is provided"
        args = ["label_command"]
        out, err = self.run_manage(args)
        self.assertOutput(err, "Enter at least one label")