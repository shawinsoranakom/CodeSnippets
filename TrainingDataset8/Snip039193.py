def test_submit_button_primary_type(self):
        """Test that a submit button can be called with type="primary"."""

        form = st.form("foo")
        form.form_submit_button(type="primary")

        last_delta = self.get_delta_from_queue()
        self.assertEqual("primary", last_delta.new_element.button.type)