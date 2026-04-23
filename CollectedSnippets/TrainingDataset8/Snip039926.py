def test_getitem_reserved_key(self):
        with pytest.raises(StreamlitAPIException):
            _ = self.session_state_proxy[self.reserved_key]