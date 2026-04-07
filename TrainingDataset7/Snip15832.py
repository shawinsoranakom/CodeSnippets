def test_noargs_with_args(self):
        "NoArg Commands raise an error if an argument is provided"
        args = ["noargs_command", "argument"]
        out, err = self.run_manage(args)
        self.assertOutput(err, "error: unrecognized arguments: argument")