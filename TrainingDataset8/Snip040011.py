def test_get(self):
        states = WidgetStates()

        _create_widget("trigger", states).trigger_value = True
        _create_widget("bool", states).bool_value = True
        _create_widget("float", states).double_value = 0.5
        _create_widget("int", states).int_value = 123
        _create_widget("string", states).string_value = "howdy!"

        session_state = SessionState()
        session_state.set_widgets_from_proto(states)

        session_state._set_widget_metadata(create_metadata("trigger", "trigger_value"))
        session_state._set_widget_metadata(create_metadata("bool", "bool_value"))
        session_state._set_widget_metadata(create_metadata("float", "double_value"))
        session_state._set_widget_metadata(create_metadata("int", "int_value"))
        session_state._set_widget_metadata(create_metadata("string", "string_value"))

        self.assertEqual(True, session_state["trigger"])
        self.assertEqual(True, session_state["bool"])
        self.assertAlmostEqual(0.5, session_state["float"])
        self.assertEqual(123, session_state["int"])
        self.assertEqual("howdy!", session_state["string"])