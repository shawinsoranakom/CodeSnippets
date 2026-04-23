def test_headless_telemetry_message(self, headless_mode):
        """If headless mode, show a message about usage metrics gathering."""

        with testutil.patch_config_options({"server.headless": headless_mode}):
            with patch("validators.url", return_value=False), patch(
                "os.path.exists", return_value=True
            ), patch("streamlit.config.is_manually_set", return_value=False), patch(
                "streamlit.runtime.credentials._check_credential_file_exists",
                return_value=False,
            ):
                result = self.runner.invoke(cli, ["run", "file_name.py"])

            self.assertNotEqual(0, result.exit_code)
            self.assertEqual(
                "Collecting usage statistics" in result.output,
                headless_mode,  # Should only be shown if n headless mode
            )