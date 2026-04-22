def test_defaults(self, defaults, expected):
        """Test that valid default can be passed as expected."""
        st.multiselect("the label", ["Coffee", "Tea", "Water"], defaults)

        c = self.get_delta_from_queue().new_element.multiselect
        self.assertEqual(c.label, "the label")
        self.assertListEqual(c.default[:], expected)
        self.assertEqual(c.options, ["Coffee", "Tea", "Water"])