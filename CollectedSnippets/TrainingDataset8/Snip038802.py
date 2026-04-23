def test_value_types(self, arg_value, proto_value):
        """Test that it supports different types of values."""
        st.date_input("the label", arg_value)

        c = self.get_delta_from_queue().new_element.date_input
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, proto_value)