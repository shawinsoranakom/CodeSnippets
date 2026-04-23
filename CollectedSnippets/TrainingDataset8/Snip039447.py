def test_Credentials_load_empty(self):
        """Test Credentials.load() with empty email"""
        data = textwrap.dedent(
            """
            [general]
            email = ""
        """
        ).strip()
        m = mock_open(read_data=data)
        with patch("streamlit.runtime.credentials.open", m, create=True):
            c = Credentials.get_current()
            c.load()
            self.assertEqual("", c.activation.email)