def test_marshall_excludes_widgets_without_state(self):
        widget_states = WidgetStates()
        _create_widget("trigger", widget_states).trigger_value = True

        session_state = SessionState()
        session_state.set_widgets_from_proto(widget_states)
        session_state._set_widget_metadata(
            WidgetMetadata("other_widget", lambda x, s: x, None, "trigger_value", True)
        )

        widgets = session_state.get_widget_states()

        self.assertEqual(len(widgets), 1)
        self.assertEqual(widgets[0].id, "trigger")