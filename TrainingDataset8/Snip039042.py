def test_invalid_value_range(self):
        """Test that value must be within the length of the options."""
        with self.assertRaises(StreamlitAPIException):
            st.radio("the label", ("m", "f"), 2)