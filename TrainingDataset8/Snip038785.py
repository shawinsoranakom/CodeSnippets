def test_just_label(self):
        """Test that it can be called with no value."""
        st.checkbox("the label")

        c = self.get_delta_from_queue().new_element.checkbox
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, False)
        self.assertEqual(c.disabled, False)