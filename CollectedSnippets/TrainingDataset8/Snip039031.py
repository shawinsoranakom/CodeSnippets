def test_just_label(self):
        """Test that it can be called with no value."""
        st.radio("the label", ("m", "f"))

        c = self.get_delta_from_queue().new_element.radio
        self.assertEqual(c.label, "the label")
        self.assertEqual(
            c.label_visibility.value,
            LabelVisibilityMessage.LabelVisibilityOptions.VISIBLE,
        )
        self.assertEqual(c.default, 0)
        self.assertEqual(c.disabled, False)