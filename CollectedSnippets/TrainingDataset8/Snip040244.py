def test_run_existing_file_argument(self):
        """streamlit run succeeds if an existing file is passed."""
        with patch("validators.url", return_value=False), patch(
            "streamlit.web.cli._main_run"
        ), patch("os.path.exists", return_value=True):

            result = self.runner.invoke(cli, ["run", "file_name.py"])
        self.assertEqual(0, result.exit_code)