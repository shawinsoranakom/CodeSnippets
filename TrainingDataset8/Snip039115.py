def test_just_label(self):
        """Test that it can be called with no value."""
        st.text_input("the label")

        c = self.get_delta_from_queue().new_element.text_input
        self.assertEqual(c.label, "the label")
        self.assertEqual(
            c.label_visibility.value,
            LabelVisibilityMessage.LabelVisibilityOptions.VISIBLE,
        )
        self.assertEqual(c.default, "")
        self.assertEqual(c.type, TextInput.DEFAULT)
        self.assertEqual(c.disabled, False)