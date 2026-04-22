def test_options_with_default_types(
        self, options, defaults, expected_options, expected_default
    ):
        st.multiselect("label", options, defaults)

        c = self.get_delta_from_queue().new_element.multiselect
        self.assertEqual(c.label, "label")
        self.assertListEqual(c.default[:], expected_default)
        self.assertEqual(c.options, expected_options)