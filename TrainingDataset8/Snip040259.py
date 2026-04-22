def test_version_command(self):
        """Tests the version command redirects to using the --version flag"""
        with patch.object(sys, "argv", ["streamlit", "version"]) as args:
            self.runner.invoke(cli, ["version"])
            self.assertEqual("--version", args[1])