def test_call_callbacks(self):
        """Test the call_callbacks method in 6 possible cases:

        1. A widget does not have a callback
        2. A widget's old and new values are equal, so the callback is not
           called.
        3. A widget's callback has no args provided.
        4. A widget's callback has just args provided.
        5. A widget's callback has just kwargs provided.
        6. A widget's callback has both args and kwargs provided.
        """
        prev_states = WidgetStates()
        _create_widget("trigger", prev_states).trigger_value = True
        _create_widget("bool", prev_states).bool_value = True
        _create_widget("bool2", prev_states).bool_value = True
        _create_widget("float", prev_states).double_value = 0.5
        _create_widget("int", prev_states).int_value = 123
        _create_widget("string", prev_states).string_value = "howdy!"

        session_state = SessionState()
        session_state.set_widgets_from_proto(prev_states)

        mock_callback = MagicMock()
        deserializer = lambda x, s: x

        callback_cases = [
            ("trigger", "trigger_value", None, None, None),
            ("bool", "bool_value", mock_callback, None, None),
            ("bool2", "bool_value", mock_callback, None, None),
            ("float", "double_value", mock_callback, (1,), None),
            ("int", "int_value", mock_callback, None, {"x": 2}),
            ("string", "string_value", mock_callback, (1,), {"x": 2}),
        ]
        for widget_id, value_type, callback, args, kwargs in callback_cases:
            session_state._set_widget_metadata(
                WidgetMetadata(
                    widget_id,
                    deserializer,
                    lambda x: x,
                    value_type=value_type,
                    callback=callback,
                    callback_args=args,
                    callback_kwargs=kwargs,
                )
            )

        states = WidgetStates()
        _create_widget("trigger", states).trigger_value = True
        _create_widget("bool", states).bool_value = True
        _create_widget("bool2", states).bool_value = False
        _create_widget("float", states).double_value = 1.5
        _create_widget("int", states).int_value = 321
        _create_widget("string", states).string_value = "!ydwoh"

        session_state.on_script_will_rerun(states)

        mock_callback.assert_has_calls([call(), call(1), call(x=2), call(1, x=2)])