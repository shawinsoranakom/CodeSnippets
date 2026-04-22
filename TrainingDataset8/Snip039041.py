def test_invalid_value(self):
        """Test that value must be an int."""
        with self.assertRaises(StreamlitAPIException):
            st.radio("the label", ("m", "f"), "1")