def test_run_non_existing_file_argument(self):
        """streamlit run should fail if a non existing file is passed."""

        with patch("validators.url", return_value=False), patch(
            "streamlit.web.cli._main_run"
        ), patch("os.path.exists", return_value=False):

            result = self.runner.invoke(cli, ["run", "file_name.py"])
        self.assertNotEqual(0, result.exit_code)
        self.assertIn("File does not exist", result.output)