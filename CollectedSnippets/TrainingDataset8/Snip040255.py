def test_credentials_headless_no_config(self):
        """If headless mode and no config is present,
        activation should be None."""
        with testutil.patch_config_options({"server.headless": True}):
            with patch("validators.url", return_value=False), patch(
                "streamlit.web.bootstrap.run"
            ), patch("os.path.exists", return_value=True), patch(
                "streamlit.runtime.credentials._check_credential_file_exists",
                return_value=False,
            ):
                result = self.runner.invoke(cli, ["run", "some script.py"])
            from streamlit.runtime.credentials import Credentials

            credentials = Credentials.get_current()
            self.assertIsNone(credentials.activation)
            self.assertEqual(0, result.exit_code)