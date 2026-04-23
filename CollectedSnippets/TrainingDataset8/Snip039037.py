def test_option_types(self, options, proto_options):
        """Test that it supports different types of options."""
        st.radio("the label", options)

        c = self.get_delta_from_queue().new_element.radio
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, 0)
        self.assertEqual(c.options, proto_options)