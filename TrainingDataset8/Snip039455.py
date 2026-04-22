def test_Credentials_activate_already_activated(self):
        """Test Credentials.activate() already activated."""
        c = Credentials.get_current()
        c.activation = _Activation("some_email", True)
        with patch("streamlit.runtime.credentials.LOGGER") as p:
            with pytest.raises(SystemExit):
                c.activate()
            self.assertEqual(p.error.call_count, 2)
            self.assertEqual(p.error.call_args_list[1], call("Already activated"))