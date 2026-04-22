def test_missing_toml_error(self, mock_st_error):
        """Secrets access raises an error, and calls st.error, if
        secrets.toml is missing.
        """
        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = FileNotFoundError()

            with self.assertRaises(OSError):
                self.secrets.get("no_such_secret", None)

        mock_st_error.assert_called_once_with(
            f"Secrets file not found. Expected at: {MOCK_SECRETS_FILE_LOC}"
        )