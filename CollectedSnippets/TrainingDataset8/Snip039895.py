def test_secrets_file_location(self):
        """Verify that we're looking for secrets.toml in the right place."""
        self.assertEqual(os.path.abspath("./.streamlit/secrets.toml"), SECRETS_FILE_LOC)