def test_delattr(self):
        del self.session_state_proxy.foo
        assert "foo" not in self.session_state_proxy