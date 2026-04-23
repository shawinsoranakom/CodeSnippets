def test_run_non_existing_url(self, temp_dir):
        """streamlit run should fail if a non existing but valid
        url is passed.
        """

        with patch("validators.url", return_value=True), patch(
            "streamlit.web.cli._main_run"
        ), requests_mock.mock() as m:

            m.get("http://url/app.py", exc=requests.exceptions.RequestException)
            with patch("streamlit.temporary_directory.TemporaryDirectory") as mock_tmp:
                mock_tmp.return_value.__enter__.return_value = temp_dir.path
                result = self.runner.invoke(cli, ["run", "http://url/app.py"])

        self.assertNotEqual(0, result.exit_code)
        self.assertIn("Unable to fetch", result.output)