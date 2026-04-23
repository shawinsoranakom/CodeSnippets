def test_delitem(self):
        del self.session_state["foo"]
        assert "foo" not in self.session_state