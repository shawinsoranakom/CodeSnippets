def test_Credentials_load_twice(self):
        """Test Credentials.load() called twice."""
        c = Credentials.get_current()
        c.activation = _Activation("some_email", True)
        with patch("streamlit.runtime.credentials.LOGGER") as p:
            c.load()
            p.error.assert_called_once_with(
                "Credentials already loaded. Not rereading file."
            )