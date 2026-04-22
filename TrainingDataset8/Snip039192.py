def test_submit_button_default_type(self):
        """Test that a submit button with no explicit type has default of "secondary"."""

        form = st.form("foo")
        form.form_submit_button()

        last_delta = self.get_delta_from_queue()
        self.assertEqual("secondary", last_delta.new_element.button.type)