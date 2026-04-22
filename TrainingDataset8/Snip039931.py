def test_delattr_reserved_key(self):
        with pytest.raises(StreamlitAPIException):
            delattr(self.session_state_proxy, self.reserved_key)