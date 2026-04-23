def test_Credentials_check_activated_false(self):
        """Test Credentials.check_activated() not activated."""
        c = Credentials.get_current()
        c.activation = _Activation("some_email", False)
        with patch("streamlit.runtime.credentials._exit") as p:
            c._check_activated(auto_resolve=False)
            p.assert_called_once_with("Activation email not valid.")