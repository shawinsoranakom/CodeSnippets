def test_callbacks_with_experimental_rerun(self, patched_warning):
        """Calling 'experimental_rerun' from within a widget callback
        is disallowed and results in a warning.
        """

        # A mock on_changed handler for our checkbox. It will call
        # `st.experimental_rerun`, which should result in a warning
        # being printed to the user's app.
        mock_on_checkbox_changed = MagicMock(side_effect=st.experimental_rerun)

        st.checkbox("the checkbox", on_change=mock_on_checkbox_changed)

        session_state = _raw_session_state()

        # Pretend that the checkbox has a new state value
        checkbox_state = WidgetStateProto()
        checkbox_state.id = list(session_state._new_widget_state.keys())[0]
        checkbox_state.bool_value = True
        widget_states = WidgetStatesProto()
        widget_states.widgets.append(checkbox_state)

        # Tell session_state to call our callbacks.
        session_state.on_script_will_rerun(widget_states)

        mock_on_checkbox_changed.assert_called_once()
        patched_warning.assert_called_once()