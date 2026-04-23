def test_no_value(self):
        """Test that it can be called with no value."""
        st.select_slider("the label", options=["red", "orange", "yellow"])

        c = self.get_delta_from_queue().new_element.slider
        self.assertEqual(c.label, "the label")
        self.assertEqual(
            c.label_visibility.value,
            LabelVisibilityMessage.LabelVisibilityOptions.VISIBLE,
        )
        self.assertEqual(c.default, [0])
        self.assertEqual(c.min, 0)
        self.assertEqual(c.max, 2)
        self.assertEqual(c.step, 1)