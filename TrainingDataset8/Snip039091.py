def test_value_types(self, value, proto_value, return_value):
        """Test that it supports different types of values."""
        ret = st.slider("the label", value=value)

        self.assertEqual(ret, return_value)

        c = self.get_delta_from_queue().new_element.slider
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, proto_value)