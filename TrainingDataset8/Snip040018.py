def test_coalesce_widget_states(self):
        session_state = SessionState()

        old_states = WidgetStates()

        _create_widget("old_set_trigger", old_states).trigger_value = True
        _create_widget("old_unset_trigger", old_states).trigger_value = False
        _create_widget("missing_in_new", old_states).int_value = 123
        _create_widget("shape_changing_trigger", old_states).trigger_value = True

        session_state._set_widget_metadata(
            create_metadata("old_set_trigger", "trigger_value")
        )
        session_state._set_widget_metadata(
            create_metadata("old_unset_trigger", "trigger_value")
        )
        session_state._set_widget_metadata(
            create_metadata("missing_in_new", "int_value")
        )
        session_state._set_widget_metadata(
            create_metadata("shape changing trigger", "trigger_value")
        )

        new_states = WidgetStates()

        _create_widget("old_set_trigger", new_states).trigger_value = False
        _create_widget("new_set_trigger", new_states).trigger_value = True
        _create_widget("added_in_new", new_states).int_value = 456
        _create_widget("shape_changing_trigger", new_states).int_value = 3
        session_state._set_widget_metadata(
            create_metadata("new_set_trigger", "trigger_value")
        )
        session_state._set_widget_metadata(create_metadata("added_in_new", "int_value"))
        session_state._set_widget_metadata(
            create_metadata("shape_changing_trigger", "int_value")
        )

        session_state.set_widgets_from_proto(
            coalesce_widget_states(old_states, new_states)
        )

        self.assertRaises(KeyError, lambda: session_state["old_unset_trigger"])
        self.assertRaises(KeyError, lambda: session_state["missing_in_new"])

        self.assertEqual(True, session_state["old_set_trigger"])
        self.assertEqual(True, session_state["new_set_trigger"])
        self.assertEqual(456, session_state["added_in_new"])

        # Widgets that were triggers before, but no longer are, will *not*
        # be coalesced
        self.assertEqual(3, session_state["shape_changing_trigger"])