def test_setitem(self):
        assert not self.session_state.is_new_state_value("corge")
        self.session_state["corge"] = "grault2"
        assert self.session_state["corge"] == "grault2"
        assert self.session_state.is_new_state_value("corge")