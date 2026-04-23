def test_type(self):
        """Test that it can be called with type param."""
        st.button("the label", type="primary")

        c = self.get_delta_from_queue().new_element.button
        self.assertEqual(c.type, "primary")