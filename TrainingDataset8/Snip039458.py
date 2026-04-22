def test_Credentials_reset(self):
        """Test Credentials.reset()."""
        c = Credentials.get_current()

        with patch("streamlit.runtime.credentials.os.remove") as p:
            Credentials.reset()
            p.assert_called_once_with("/mock/home/folder/.streamlit/credentials.toml")

        self.assertEqual(c, Credentials.get_current())