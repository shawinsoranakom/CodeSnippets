def test_option_types(self, options, proto_options):
        """Test that it supports different types of options."""
        st.multiselect("the label", options)

        c = self.get_delta_from_queue().new_element.multiselect
        self.assertEqual(c.label, "the label")
        self.assertListEqual(c.default[:], [])
        self.assertEqual(c.options, proto_options)