def test_to_dict(self):
        assert self.session_state_proxy.to_dict() == {"foo": "bar"}