def test_help_commands(self):
        "help --commands shows the list of all available commands"
        args = ["help", "--commands"]
        out, err = self.run_manage(args)
        self.assertNotInOutput(out, "usage:")
        self.assertNotInOutput(out, "Options:")
        self.assertNotInOutput(out, "[django]")
        self.assertOutput(out, "startapp")
        self.assertOutput(out, "startproject")
        self.assertNotInOutput(out, "\n\n")