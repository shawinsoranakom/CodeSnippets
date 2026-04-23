def test_just_label(self):
        """Test that it can be called with no value."""
        st.color_picker("the label")

        c = self.get_delta_from_queue().new_element.color_picker
        self.assertEqual(c.label, "the label")
        self.assertEqual(
            c.label_visibility.value,
            LabelVisibilityMessage.LabelVisibilityOptions.VISIBLE,
        )
        self.assertEqual(c.default, "#000000")
        self.assertEqual(c.disabled, False)