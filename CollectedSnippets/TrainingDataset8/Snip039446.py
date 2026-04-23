def test_Credentials_load(self):
        """Test Credentials.load()."""
        data = textwrap.dedent(
            """
            [general]
            email = "user@domain.com"
        """
        ).strip()
        m = mock_open(read_data=data)
        with patch("streamlit.runtime.credentials.open", m, create=True):
            c = Credentials.get_current()
            c.load()
            self.assertEqual("user@domain.com", c.activation.email)