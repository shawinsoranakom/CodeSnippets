def test_just_label(self, data):
        """Test that it can be called with label and string or bytes data."""
        st.download_button("the label", data=data)

        c = self.get_delta_from_queue().new_element.download_button
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.disabled, False)