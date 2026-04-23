def test_compact(self):
        self.session_state._compact_state()
        assert self.session_state._old_state == {
            "foo": "bar2",
            "baz": "qux2",
            "corge": "grault",
            f"{GENERATED_WIDGET_KEY_PREFIX}-foo-None": "bar",
        }
        assert self.session_state._new_session_state == {}
        assert self.session_state._new_widget_state == WStates()