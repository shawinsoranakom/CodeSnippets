def test_placeholder(self):
        """Test that it can be called with placeholder"""
        st.text_area("the label", "", placeholder="testing")

        c = self.get_delta_from_queue().new_element.text_area
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, "")
        self.assertEqual(c.placeholder, "testing")