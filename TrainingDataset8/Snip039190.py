def test_submit_button_inside_form(self):
        """Test that a submit button is allowed inside a form."""

        with st.form("foo"):
            st.form_submit_button()

        last_delta = self.get_delta_from_queue()
        self.assertEqual("foo", last_delta.new_element.button.form_id)