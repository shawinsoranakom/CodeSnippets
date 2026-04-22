def test_credentials_headless_with_config(self, headless_mode):
        """If headless, but a config file is present, activation should be
        defined.
        So we call `_check_activated`.
        """
        with testutil.patch_config_options({"server.headless": headless_mode}):
            with patch("validators.url", return_value=False), patch(
                "streamlit.web.bootstrap.run"
            ), patch("os.path.exists", return_value=True), mock.patch(
                "streamlit.runtime.credentials.Credentials._check_activated"
            ) as mock_check, patch(
                "streamlit.runtime.credentials._check_credential_file_exists",
                return_value=True,
            ):
                result = self.runner.invoke(cli, ["run", "some script.py"])
            self.assertTrue(mock_check.called)
            self.assertEqual(0, result.exit_code)