def test_value_types(self, arg_value, proto_value):
        """Test that it supports different types of values."""
        st.color_picker("the label", arg_value)

        c = self.get_delta_from_queue().new_element.color_picker
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, proto_value)