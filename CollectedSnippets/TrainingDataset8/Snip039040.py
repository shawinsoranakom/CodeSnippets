def test_no_options(self, options):
        """Test that it handles no options."""
        st.radio("the label", options)

        c = self.get_delta_from_queue().new_element.radio
        self.assertEqual(c.label, "the label")
        self.assertEqual(
            c.label_visibility.value,
            LabelVisibilityMessage.LabelVisibilityOptions.VISIBLE,
        )
        self.assertEqual(c.default, 0)
        self.assertEqual(c.options, [])