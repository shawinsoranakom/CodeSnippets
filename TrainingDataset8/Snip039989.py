def test_filtered_state(self):
        assert self.session_state.filtered_state == {
            "foo": "bar2",
            "baz": "qux2",
            "corge": "grault",
        }