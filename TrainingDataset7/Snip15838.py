def test_label_command(self):
        "User LabelCommands can execute when a label is provided"
        args = ["label_command", "testlabel"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        self.assertOutput(
            out,
            "EXECUTE:LabelCommand label=testlabel, options=[('force_color', "
            "False), ('no_color', False), ('pythonpath', None), ('settings', "
            "None), ('traceback', False), ('verbosity', 1)]",
        )