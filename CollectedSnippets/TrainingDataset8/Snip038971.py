def test_just_label(self):
        """Test that it can be called with no value."""
        st.multiselect("the label", ("m", "f"))

        c = self.get_delta_from_queue().new_element.multiselect
        self.assertEqual(c.label, "the label")
        self.assertEqual(
            c.label_visibility.value,
            LabelVisibilityMessage.LabelVisibilityOptions.VISIBLE,
        )
        self.assertListEqual(c.default[:], [])
        self.assertEqual(c.disabled, False)