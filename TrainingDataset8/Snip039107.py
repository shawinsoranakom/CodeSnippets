def test_height(self):
        """Test that it can be called with height"""
        st.text_area("the label", "", 300)

        c = self.get_delta_from_queue().new_element.text_area
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, "")
        self.assertEqual(c.height, 300)