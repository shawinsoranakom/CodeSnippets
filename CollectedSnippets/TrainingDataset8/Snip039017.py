def test_should_keep_type_of_return_value_after_rerun(self):
        # Generate widget id and reset context
        st.number_input("a number", min_value=1, max_value=100, key="number")
        widget_id = self.new_script_run_ctx.session_state.get_widget_states()[0].id
        self.new_script_run_ctx.reset()

        # Set the state of the widgets to the test state
        widget_state = WidgetState()
        widget_state.id = widget_id
        widget_state.double_value = 42.0
        self.new_script_run_ctx.session_state._state._new_widget_state.set_widget_from_proto(
            widget_state
        )

        # Render widget again with the same parameters
        number = st.number_input("a number", min_value=1, max_value=100, key="number")

        # Assert output
        self.assertEqual(number, 42)
        self.assertEqual(type(number), int)