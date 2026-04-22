def test_default_types(self, defaults, expected):
        """Test that iterables other than lists can be passed as defaults."""
        st.multiselect("the label", ["Coffee", "Tea", "Water"], defaults)

        c = self.get_delta_from_queue().new_element.multiselect
        self.assertEqual(c.label, "the label")
        self.assertListEqual(c.default[:], expected)
        self.assertEqual(c.options, ["Coffee", "Tea", "Water"])