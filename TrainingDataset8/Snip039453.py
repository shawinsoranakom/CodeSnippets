def test_Credentials_check_activated_error(self):
        """Test Credentials.check_activated() has an error."""
        c = Credentials.get_current()
        c.activation = _Activation("some_email", True)
        with patch.object(c, "load", side_effect=Exception("Some error")), patch(
            "streamlit.runtime.credentials._exit"
        ) as p:
            c._check_activated(auto_resolve=False)
            p.assert_called_once_with("Some error")