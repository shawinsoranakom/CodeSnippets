def test_getattr_error(self):
        with pytest.raises(AttributeError):
            del self.session_state_proxy.nonexistent