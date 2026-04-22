def test_getattr(self):
        assert self.session_state_proxy.foo == "bar"