def test_setattr(self):
        self.session_state_proxy.corge = "grault2"
        assert self.session_state_proxy.corge == "grault2"