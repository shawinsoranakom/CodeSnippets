def test_setattr_reserved_key(self):
        with pytest.raises(StreamlitAPIException):
            setattr(self.session_state_proxy, self.reserved_key, "foo")