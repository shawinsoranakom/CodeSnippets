def test_options_types(self, value, options, default):
        """Test that it supports different types of options."""

        st.select_slider("the label", value=value, options=options)

        c = self.get_delta_from_queue().new_element.slider
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, default)