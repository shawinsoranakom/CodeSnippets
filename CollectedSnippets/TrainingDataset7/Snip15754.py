def test_custom_command(self):
        "alternate: manage.py can't execute user commands without settings"
        args = ["noargs_command"]
        out, err = self.run_manage(args)
        self.assertNoOutput(out)
        self.assertOutput(
            err, r"No module named '?(test_project\.)?settings'?", regex=True
        )