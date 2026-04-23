def test_setitem_reserved_key(self):
        with pytest.raises(StreamlitAPIException):
            self.session_state_proxy[self.reserved_key] = "foo"