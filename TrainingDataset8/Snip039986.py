def setUp(self):
        old_state = {"foo": "bar", "baz": "qux", "corge": "grault"}
        new_session_state = {"foo": "bar2"}
        new_widget_state = WStates(
            {
                "baz": Value("qux2"),
                f"{GENERATED_WIDGET_KEY_PREFIX}-foo-None": Value("bar"),
            },
        )
        self.session_state = SessionState(
            old_state, new_session_state, new_widget_state
        )