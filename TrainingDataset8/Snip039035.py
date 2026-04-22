def test_valid_value(self):
        """Test that valid value is an int."""
        st.radio("the label", ("m", "f"), 1)

        c = self.get_delta_from_queue().new_element.radio
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, 1)