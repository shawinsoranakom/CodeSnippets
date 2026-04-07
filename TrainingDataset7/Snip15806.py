def test_help(self):
        "help is handled as a special case"
        args = ["help"]
        out, err = self.run_manage(args)
        self.assertOutput(
            out, "Type 'manage.py help <subcommand>' for help on a specific subcommand."
        )
        self.assertOutput(out, "[django]")
        self.assertOutput(out, "startapp")
        self.assertOutput(out, "startproject")