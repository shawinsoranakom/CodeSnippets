def test_disabled_submit_button(self):
        """Test that a submit button can be disabled."""

        with st.form("foo"):
            st.form_submit_button(disabled=True)

        last_delta = self.get_delta_from_queue()
        self.assertEqual(True, last_delta.new_element.button.disabled)