def test_just_label(self):
        """Test that it can be called with no value."""
        st.number_input("the label")

        c = self.get_delta_from_queue().new_element.number_input
        self.assertEqual(c.label, "the label")
        self.assertEqual(
            c.label_visibility.value,
            LabelVisibilityMessage.LabelVisibilityOptions.VISIBLE,
        )
        self.assertEqual(c.default, 0.0)
        self.assertEqual(c.has_min, False)
        self.assertEqual(c.has_max, False)
        self.assertEqual(c.disabled, False)