def test_no_warning_with_value_set_in_state(self, patched_get_session_state):
        mock_session_state = MagicMock()
        mock_session_state.is_new_state_value.return_value = True
        patched_get_session_state.return_value = mock_session_state

        st.number_input("the label", min_value=1, max_value=10, key="number_input")

        c = self.get_delta_from_queue().new_element.number_input
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, 1)

        # Assert that no warning delta is enqueued when setting the widget
        # value via st.session_state.
        self.assertEqual(len(self.get_all_deltas_from_queue()), 1)