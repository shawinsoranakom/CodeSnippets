def test_filtered_state_resilient_to_missing_metadata(self):
        old_state = {"foo": "bar", "corge": "grault"}
        new_session_state = {}
        new_widget_state = WStates(
            {f"{GENERATED_WIDGET_KEY_PREFIX}-baz": Serialized(WidgetStateProto())},
        )
        self.session_state = SessionState(
            old_state, new_session_state, new_widget_state
        )

        assert self.session_state.filtered_state == {
            "foo": "bar",
            "corge": "grault",
        }