def test_getattr_reserved_key(self):
        with pytest.raises(StreamlitAPIException):
            getattr(self.session_state_proxy, self.reserved_key)