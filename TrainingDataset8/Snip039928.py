def test_delitem_reserved_key(self):
        with pytest.raises(StreamlitAPIException):
            del self.session_state_proxy[self.reserved_key]