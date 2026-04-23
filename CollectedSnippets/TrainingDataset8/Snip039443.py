def test_Credentials_constructor(self):
        """Test Credentials constructor."""
        c = Credentials()

        self.assertEqual(c._conf_file, "/mock/home/folder/.streamlit/credentials.toml")
        self.assertEqual(c.activation, None)