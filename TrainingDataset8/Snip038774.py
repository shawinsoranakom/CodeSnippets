def test_button(self):
        """Test that it can be called."""
        st.button("the label")

        c = self.get_delta_from_queue().new_element.button
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, False)
        self.assertEqual(c.form_id, "")
        self.assertEqual(c.type, "secondary")
        self.assertEqual(c.is_form_submitter, False)
        self.assertEqual(c.disabled, False)