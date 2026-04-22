def test_no_options(self, options):
        """Test that it handles no options."""
        st.multiselect("the label", options)

        c = self.get_delta_from_queue().new_element.multiselect
        self.assertEqual(c.label, "the label")
        self.assertListEqual(c.default[:], [])
        self.assertEqual(c.options, [])