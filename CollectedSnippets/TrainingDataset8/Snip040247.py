def test_run_valid_url(self, temp_dir):
        """streamlit run succeeds if an existing url is passed."""

        with patch("validators.url", return_value=True), patch(
            "streamlit.web.cli._main_run"
        ), requests_mock.mock() as m:

            file_content = b"content"
            m.get("http://url/app.py", content=file_content)
            with patch("streamlit.temporary_directory.TemporaryDirectory") as mock_tmp:
                mock_tmp.return_value.__enter__.return_value = temp_dir.path
                result = self.runner.invoke(cli, ["run", "http://url/app.py"])
                with open(os.path.join(temp_dir.path, "app.py"), "rb") as f:
                    self.assertEqual(file_content, f.read())

        self.assertEqual(0, result.exit_code)