def test_help_command(self):
        """Tests the help command redirects to using the --help flag"""
        with patch.object(sys, "argv", ["streamlit", "help"]) as args:
            self.runner.invoke(cli, ["help"])
            self.assertEqual("--help", args[1])