def test_reset_triggers(self):
        states = WidgetStates()
        session_state = SessionState()

        _create_widget("trigger", states).trigger_value = True
        _create_widget("int", states).int_value = 123
        session_state.set_widgets_from_proto(states)
        session_state._set_widget_metadata(
            WidgetMetadata("trigger", lambda x, s: x, None, "trigger_value")
        )
        session_state._set_widget_metadata(
            WidgetMetadata("int", lambda x, s: x, None, "int_value")
        )

        self.assertTrue(session_state["trigger"])
        self.assertEqual(123, session_state["int"])

        session_state._reset_triggers()

        self.assertFalse(session_state["trigger"])
        self.assertEqual(123, session_state["int"])