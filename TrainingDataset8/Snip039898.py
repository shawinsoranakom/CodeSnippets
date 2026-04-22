def test_malformed_toml_error(self, mock_st_error, _):
        """Secrets access raises an error, and calls st.error, if
        secrets.toml is malformed.
        """
        with self.assertRaises(TomlDecodeError):
            self.secrets.get("no_such_secret", None)

        mock_st_error.assert_called_once_with("Error parsing Secrets file.")