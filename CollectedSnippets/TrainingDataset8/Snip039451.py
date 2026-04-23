def test_Credentials_check_activated_already_loaded(self):
        """Test Credentials.check_activated() already loaded."""
        c = Credentials.get_current()
        c.activation = _Activation("some_email", True)
        with patch("streamlit.runtime.credentials._exit") as p:
            c._check_activated(auto_resolve=False)
            p.assert_not_called()