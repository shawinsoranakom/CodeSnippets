def test_submit_button_called_directly_on_form_block(self):
        """Test that a submit button can be called directly on a form block."""

        form = st.form("foo")
        form.form_submit_button()

        last_delta = self.get_delta_from_queue()
        self.assertEqual("foo", last_delta.new_element.button.form_id)